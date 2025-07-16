"""
Services pour la gestion des webhooks Stripe et PayPal
"""

import json
import time
import logging
from django.utils import timezone
from django.http import HttpResponse
from .models import WebhookLog, OrphanTransaction, Transaction
from decimal import Decimal


class WebhookLoggerService:
    """Service pour logger tous les webhooks reçus"""

    @staticmethod
    def log_webhook(
        provider,
        event_type,
        event_id,
        payload,
        signature_valid=False,
        processed_successfully=False,
        error_message="",
        processing_start_time=None,
    ):
        """Enregistre un webhook dans les logs"""

        processing_time_ms = None
        if processing_start_time:
            processing_time_ms = int((time.time() - processing_start_time) * 1000)

        try:
            WebhookLog.objects.create(
                provider=provider,
                event_type=event_type,
                event_id=event_id,
                payload=payload,
                signature_valid=signature_valid,
                processed_successfully=processed_successfully,
                error_message=error_message,
                processing_time_ms=processing_time_ms,
            )
        except Exception as e:
            # En cas d'erreur lors du logging, on log dans les fichiers
            logger = logging.getLogger("payment")
            logger.error(f"Erreur lors de l'enregistrement du webhook: {e}")


class StripeWebhookService:
    """Service pour gérer les webhooks Stripe"""

    @staticmethod
    def process_webhook(request):
        """Point d'entrée principal pour traiter les webhooks Stripe"""
        import stripe
        from django.conf import settings

        logger = logging.getLogger("payment")
        processing_start = time.time()
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        # Variables pour le logging
        event_type = "unknown"
        event_id = "unknown"
        signature_valid = False
        processed_successfully = False
        error_message = ""

        try:
            # Validation de la signature
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            signature_valid = True
            event_type = event["type"]
            event_id = event["id"]

            logger.info(f"Webhook Stripe reçu: {event_type} - ID: {event_id}")

            # Traitement de l'événement
            result = StripeWebhookService._handle_event(event, logger)
            processed_successfully = result.get("success", False)

            if not processed_successfully:
                error_message = result.get("error", "Erreur inconnue")

            return HttpResponse(status=200 if processed_successfully else 500)

        except ValueError as e:
            error_message = f"Payload invalide: {e}"
            logger.error(f"Webhook Stripe - {error_message}")
            return HttpResponse("Invalid payload", status=400)

        except stripe.error.SignatureVerificationError as e:
            error_message = f"Signature invalide: {e}"
            logger.error(f"Webhook Stripe - {error_message}")
            return HttpResponse("Invalid signature", status=400)

        except Exception as e:
            error_message = f"Erreur interne: {e}"
            logger.error(f"Erreur webhook Stripe: {error_message}", exc_info=True)
            return HttpResponse("Internal error", status=500)

        finally:
            # Logger le webhook dans tous les cas
            try:
                payload_dict = json.loads(payload.decode("utf-8")) if payload else {}
            except:
                payload_dict = {"raw_payload": str(payload)}

            WebhookLoggerService.log_webhook(
                provider="stripe",
                event_type=event_type,
                event_id=event_id,
                payload=payload_dict,
                signature_valid=signature_valid,
                processed_successfully=processed_successfully,
                error_message=error_message,
                processing_start_time=processing_start,
            )

    @staticmethod
    def _handle_event(event, logger):
        """Traite un événement Stripe spécifique"""
        event_type = event["type"]

        try:
            if event_type == "payment_intent.succeeded":
                return StripeWebhookService._handle_payment_success(event, logger)

            elif event_type == "payment_intent.payment_failed":
                return StripeWebhookService._handle_payment_failed(event, logger)

            elif event_type == "payment_intent.canceled":
                return StripeWebhookService._handle_payment_canceled(event, logger)

            elif event_type == "payment_intent.processing":
                return StripeWebhookService._handle_payment_processing(event, logger)

            elif event_type == "payment_intent.requires_action":
                return StripeWebhookService._handle_payment_requires_action(
                    event, logger
                )

            elif event_type == "charge.dispute.created":
                return StripeWebhookService._handle_dispute_created(event, logger)

            else:
                logger.info(f"Événement Stripe non traité: {event_type}")
                return {
                    "success": True,
                    "message": "Event not handled but acknowledged",
                }

        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement {event_type}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _handle_payment_success(event, logger):
        """Traite un paiement Stripe réussi"""
        from django.db import transaction as db_transaction
        from store.models import Order

        payment_intent = event["data"]["object"]
        payment_intent_id = payment_intent["id"]

        try:
            transaction = Transaction.objects.get(transaction_id=payment_intent_id)

            if transaction.status == "succeeded":
                logger.info(f"Transaction {transaction.id} déjà finalisée")
                return {"success": True, "message": "Already processed"}

            with db_transaction.atomic():
                transaction.status = "succeeded"
                transaction.updated_at = timezone.now()

                # Ajouter les détails de la réponse Stripe
                stripe_data = {
                    "payment_intent_id": payment_intent_id,
                    "amount_received": payment_intent.get("amount_received"),
                    "charges": payment_intent.get("charges", {}).get("data", []),
                    "webhook_timestamp": timezone.now().isoformat(),
                }
                transaction.provider_response = json.dumps(stripe_data)
                transaction.save()

                # Finaliser les commandes
                if transaction.order_id:
                    order_ids = [
                        int(oid.strip())
                        for oid in transaction.order_id.split(",")
                        if oid.strip().isdigit()
                    ]
                    cart_orders = Order.objects.filter(
                        id__in=order_ids, user=transaction.user, ordered=False
                    )

                    for order in cart_orders:
                        order.ordered = True
                        order.date_ordered = timezone.now()
                        order.save()

                        # Diminuer le stock
                        product = order.product
                        if product.stock >= order.quantity:
                            product.stock -= order.quantity
                            product.save()
                            logger.info(
                                f"Stock mis à jour pour {product.name}: "
                                f"-{order.quantity}"
                            )

            logger.info(f"Paiement Stripe finalisé avec succès: {transaction.id}")
            return {"success": True, "message": "Payment processed successfully"}

        except Transaction.DoesNotExist:
            logger.warning(
                f"Transaction non trouvée pour PaymentIntent: {payment_intent_id}"
            )
            # Créer une transaction orpheline
            StripeWebhookService._create_orphan_transaction(payment_intent, logger)
            return {"success": True, "message": "Orphan transaction created"}

    @staticmethod
    def _handle_payment_failed(event, logger):
        """Traite un échec de paiement Stripe"""
        payment_intent = event["data"]["object"]
        payment_intent_id = payment_intent["id"]

        try:
            transaction = Transaction.objects.get(transaction_id=payment_intent_id)
            transaction.status = "failed"
            transaction.updated_at = timezone.now()

            failure_data = {
                "last_payment_error": payment_intent.get("last_payment_error"),
                "failure_code": payment_intent.get("last_payment_error", {}).get(
                    "code"
                ),
                "failure_message": payment_intent.get("last_payment_error", {}).get(
                    "message"
                ),
                "webhook_timestamp": timezone.now().isoformat(),
            }
            transaction.provider_response = json.dumps(failure_data)
            transaction.save()

            logger.info(f"Paiement Stripe échoué: {transaction.id}")
            return {"success": True, "message": "Payment failure recorded"}

        except Transaction.DoesNotExist:
            logger.warning(f"Transaction non trouvée pour échec: {payment_intent_id}")
            return {"success": True, "message": "Transaction not found"}

    @staticmethod
    def _handle_payment_canceled(event, logger):
        """Traite l'annulation d'un paiement Stripe"""
        payment_intent = event["data"]["object"]
        payment_intent_id = payment_intent["id"]

        try:
            transaction = Transaction.objects.get(transaction_id=payment_intent_id)
            transaction.status = "cancelled"
            transaction.updated_at = timezone.now()
            transaction.save()

            logger.info(f"Paiement Stripe annulé: {transaction.id}")
            return {"success": True, "message": "Payment cancellation recorded"}

        except Transaction.DoesNotExist:
            logger.warning(
                f"Transaction non trouvée pour annulation: {payment_intent_id}"
            )
            return {"success": True, "message": "Transaction not found"}

    @staticmethod
    def _handle_payment_processing(event, logger):
        """Traite un paiement Stripe en cours"""
        payment_intent = event["data"]["object"]
        payment_intent_id = payment_intent["id"]

        try:
            transaction = Transaction.objects.get(transaction_id=payment_intent_id)
            transaction.status = "processing"
            transaction.updated_at = timezone.now()
            transaction.save()

            logger.info(f"Paiement Stripe en traitement: {transaction.id}")
            return {"success": True, "message": "Processing status updated"}

        except Transaction.DoesNotExist:
            logger.warning(
                f"Transaction non trouvée pour traitement: {payment_intent_id}"
            )
            return {"success": True, "message": "Transaction not found"}

    @staticmethod
    def _handle_payment_requires_action(event, logger):
        """Traite un paiement Stripe nécessitant une action"""
        payment_intent = event["data"]["object"]
        payment_intent_id = payment_intent["id"]

        try:
            transaction = Transaction.objects.get(transaction_id=payment_intent_id)
            transaction.status = "requires_action"
            transaction.updated_at = timezone.now()
            transaction.save()

            logger.info(f"Paiement Stripe nécessite une action: {transaction.id}")
            return {"success": True, "message": "Action required status updated"}

        except Transaction.DoesNotExist:
            logger.warning(f"Transaction non trouvée pour action: {payment_intent_id}")
            return {"success": True, "message": "Transaction not found"}

    @staticmethod
    def _handle_dispute_created(event, logger):
        """Traite la création d'un litige Stripe"""
        dispute = event["data"]["object"]
        charge_id = dispute.get("charge")

        logger.warning(
            f"Litige Stripe créé pour charge: {charge_id}, "
            f"montant: {dispute.get('amount')}"
        )

        # TODO: Implémenter la logique de gestion des litiges
        # - Créer un modèle Dispute
        # - Envoyer des notifications aux administrateurs
        # - Marquer les transactions concernées

        return {"success": True, "message": "Dispute logged"}

    @staticmethod
    def _create_orphan_transaction(payment_intent, logger):
        """Crée une transaction orpheline pour audit"""
        try:
            OrphanTransaction.objects.create(
                provider="stripe",
                provider_transaction_id=payment_intent["id"],
                amount=Decimal(payment_intent["amount"]) / 100,
                currency=payment_intent.get("currency", "eur"),
                status=payment_intent["status"],
                provider_data=payment_intent,
            )

            logger.info(
                f"Transaction orpheline créée pour Stripe: " f"{payment_intent['id']}"
            )

        except Exception as e:
            logger.error(f"Erreur lors de la création de transaction orpheline: {e}")


class PayPalWebhookService:
    """Service pour gérer les webhooks PayPal"""

    @staticmethod
    def process_webhook(request):
        """Point d'entrée principal pour traiter les webhooks PayPal"""
        logger = logging.getLogger("payment")
        processing_start = time.time()

        # Variables pour le logging
        event_type = "unknown"
        event_id = "unknown"
        signature_valid = False
        processed_successfully = False
        error_message = ""

        try:
            # Validation de la signature
            signature_valid = PayPalWebhookService._verify_signature(request)

            if not signature_valid:
                error_message = "Signature PayPal invalide"
                logger.error(error_message)
                return HttpResponse("Invalid signature", status=400)

            # Parser le payload
            payload = json.loads(request.body.decode("utf-8"))
            event_type = payload.get("event_type", "unknown")
            event_id = payload.get("id", "unknown")

            logger.info(f"Webhook PayPal reçu: {event_type} - ID: {event_id}")

            # Traitement de l'événement
            result = PayPalWebhookService._handle_event(payload, logger)
            processed_successfully = result.get("success", False)

            if not processed_successfully:
                error_message = result.get("error", "Erreur inconnue")

            return HttpResponse(status=200 if processed_successfully else 500)

        except json.JSONDecodeError as e:
            error_message = f"Payload invalide: {e}"
            logger.error(f"Webhook PayPal - {error_message}")
            return HttpResponse("Invalid JSON", status=400)

        except Exception as e:
            error_message = f"Erreur interne: {e}"
            logger.error(f"Erreur webhook PayPal: {error_message}", exc_info=True)
            return HttpResponse("Internal error", status=500)

        finally:
            # Logger le webhook
            try:
                payload_dict = json.loads(request.body.decode("utf-8"))
            except:
                payload_dict = {"raw_payload": str(request.body)}

            WebhookLoggerService.log_webhook(
                provider="paypal",
                event_type=event_type,
                event_id=event_id,
                payload=payload_dict,
                signature_valid=signature_valid,
                processed_successfully=processed_successfully,
                error_message=error_message,
                processing_start_time=processing_start,
            )

    @staticmethod
    def _verify_signature(request):
        """Vérifie la signature du webhook PayPal"""
        # TODO: Implémenter la vraie vérification de signature PayPal
        # Pour le développement, on accepte tous les webhooks
        return True

    @staticmethod
    def _handle_event(payload, logger):
        """Traite un événement PayPal spécifique"""
        event_type = payload.get("event_type")

        try:
            if event_type == "PAYMENT.CAPTURE.COMPLETED":
                return PayPalWebhookService._handle_payment_completed(payload, logger)

            elif event_type == "PAYMENT.CAPTURE.DENIED":
                return PayPalWebhookService._handle_payment_denied(payload, logger)

            elif event_type == "PAYMENT.CAPTURE.PENDING":
                return PayPalWebhookService._handle_payment_pending(payload, logger)

            elif event_type == "PAYMENT.CAPTURE.REFUNDED":
                return PayPalWebhookService._handle_payment_refunded(payload, logger)

            else:
                logger.info(f"Événement PayPal non traité: {event_type}")
                return {
                    "success": True,
                    "message": "Event not handled but acknowledged",
                }

        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'événement {event_type}: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def _handle_payment_completed(payload, logger):
        """Traite un paiement PayPal complété"""
        from django.db import transaction as db_transaction
        from store.models import Order

        resource = payload.get("resource", {})
        custom_id = resource.get("custom_id")

        if not custom_id:
            logger.warning("Pas de custom_id dans le webhook PayPal")
            return {"success": True, "message": "No custom_id found"}

        try:
            transaction = Transaction.objects.get(transaction_id=custom_id)

            if transaction.status == "succeeded":
                logger.info(f"Transaction PayPal {transaction.id} déjà finalisée")
                return {"success": True, "message": "Already processed"}

            with db_transaction.atomic():
                transaction.status = "succeeded"
                transaction.updated_at = timezone.now()

                paypal_data = {
                    "capture_id": resource.get("id"),
                    "amount": resource.get("amount"),
                    "status": resource.get("status"),
                    "webhook_timestamp": timezone.now().isoformat(),
                    "payer_email": resource.get("payer", {}).get("email_address"),
                }
                transaction.provider_response = json.dumps(paypal_data)
                transaction.save()

                # Finaliser les commandes
                if transaction.order_id:
                    order_ids = [
                        int(oid.strip())
                        for oid in transaction.order_id.split(",")
                        if oid.strip().isdigit()
                    ]
                    cart_orders = Order.objects.filter(
                        id__in=order_ids, user=transaction.user, ordered=False
                    )

                    for order in cart_orders:
                        order.ordered = True
                        order.date_ordered = timezone.now()
                        order.save()

                        # Diminuer le stock
                        product = order.product
                        if product.stock >= order.quantity:
                            product.stock -= order.quantity
                            product.save()

            logger.info(f"Paiement PayPal finalisé avec succès: {transaction.id}")
            return {"success": True, "message": "Payment processed successfully"}

        except Transaction.DoesNotExist:
            logger.warning(f"Transaction PayPal non trouvée: {custom_id}")
            return {"success": True, "message": "Transaction not found"}

    @staticmethod
    def _handle_payment_denied(payload, logger):
        """Traite un paiement PayPal refusé"""
        resource = payload.get("resource", {})
        custom_id = resource.get("custom_id")

        if not custom_id:
            return {"success": True, "message": "No custom_id found"}

        try:
            transaction = Transaction.objects.get(transaction_id=custom_id)
            transaction.status = "failed"
            transaction.updated_at = timezone.now()

            denial_data = {
                "reason_code": resource.get("status_details", {}).get("reason"),
                "webhook_timestamp": timezone.now().isoformat(),
            }
            transaction.provider_response = json.dumps(denial_data)
            transaction.save()

            logger.info(f"Paiement PayPal refusé: {transaction.id}")
            return {"success": True, "message": "Payment denial recorded"}

        except Transaction.DoesNotExist:
            logger.warning(f"Transaction PayPal non trouvée pour refus: {custom_id}")
            return {"success": True, "message": "Transaction not found"}

    @staticmethod
    def _handle_payment_pending(payload, logger):
        """Traite un paiement PayPal en attente"""
        resource = payload.get("resource", {})
        custom_id = resource.get("custom_id")

        if not custom_id:
            return {"success": True, "message": "No custom_id found"}

        try:
            transaction = Transaction.objects.get(transaction_id=custom_id)
            transaction.status = "processing"
            transaction.updated_at = timezone.now()
            transaction.save()

            logger.info(f"Paiement PayPal en attente: {transaction.id}")
            return {"success": True, "message": "Payment pending status updated"}

        except Transaction.DoesNotExist:
            logger.warning(f"Transaction PayPal non trouvée: {custom_id}")
            return {"success": True, "message": "Transaction not found"}

    @staticmethod
    def _handle_payment_refunded(payload, logger):
        """Traite un remboursement PayPal"""
        resource = payload.get("resource", {})

        logger.info(f"Remboursement PayPal traité: {resource.get('id')}")

        # TODO: Implémenter la logique de remboursement
        # - Marquer la transaction comme remboursée
        # - Remettre les produits en stock si nécessaire
        # - Envoyer des notifications

        return {"success": True, "message": "Refund logged"}
