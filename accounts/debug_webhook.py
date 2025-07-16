from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def debug_stripe_webhook(request):
    """Webhook de debug pour analyser les headers Stripe"""
    log_content = []
    log_content.append("=" * 60)
    log_content.append("🔍 DEBUG WEBHOOK STRIPE")
    log_content.append(f"Method: {request.method}")
    log_content.append(f"Content-Type: {request.META.get('CONTENT_TYPE', 'N/A')}")

    # Afficher tous les headers HTTP
    headers = {}
    for key, value in request.META.items():
        if key.startswith("HTTP_"):
            headers[key] = value

    log_content.append("Headers HTTP:")
    for key, value in headers.items():
        log_content.append(f"  {key}: {value}")

    # Signature Stripe
    stripe_signature = request.META.get("HTTP_STRIPE_SIGNATURE")
    log_content.append(f"Stripe-Signature header: {stripe_signature}")

    # Payload
    payload = request.body
    log_content.append(f"Payload length: {len(payload)} bytes")

    try:
        payload_json = json.loads(payload.decode("utf-8"))
        log_content.append(f"Event type: {payload_json.get('type', 'N/A')}")
        log_content.append(f"Event id: {payload_json.get('id', 'N/A')}")
    except Exception as e:
        log_content.append(f"Payload non JSON: {e}")

    # TEST DE VALIDATION STRIPE
    if stripe_signature and payload:
        log_content.append("\n🧪 TEST VALIDATION SIGNATURE:")
        try:
            import stripe
            from django.conf import settings

            event = stripe.Webhook.construct_event(
                payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
            )
            log_content.append("✅ Signature Stripe VALIDE!")
            log_content.append(f"   Event validé: {event['type']} - {event['id']}")
        except stripe.error.SignatureVerificationError as e:
            log_content.append(f"❌ Signature Stripe INVALIDE: {e}")
        except Exception as e:
            log_content.append(f"🚨 Erreur validation: {e}")

    log_content.append("=" * 60)

    # Écrire dans un fichier de log
    import os

    log_file = os.path.join(os.path.dirname(__file__), "..", "webhook_debug.log")
    with open(log_file, "a") as f:
        f.write("\n".join(log_content) + "\n\n")

    # Aussi dans la console
    for line in log_content:
        print(line)

    return HttpResponse("OK", status=200)
