"""
Vues d'administration personnalisées pour le système de paiements
"""

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count, Sum, Q
from datetime import timedelta
from .models import Transaction, WebhookLog, OrphanTransaction, PaymentMethod


@staff_member_required
def payments_dashboard(request):
    """Dashboard personnalisé pour le système de paiements"""

    # Calcul des statistiques
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Statistiques des transactions
    total_transactions = Transaction.objects.count()
    successful_transactions = Transaction.objects.filter(
        status="succeeded", created_at__gte=thirty_days_ago
    ).count()

    # Statistiques des webhooks
    total_webhooks = WebhookLog.objects.count()
    successful_webhooks = WebhookLog.objects.filter(processed_successfully=True).count()

    webhook_success_rate = 0
    if total_webhooks > 0:
        webhook_success_rate = round((successful_webhooks / total_webhooks) * 100, 1)

    # Transactions orphelines
    orphan_transactions = OrphanTransaction.objects.count()
    uninvestigated_orphans = OrphanTransaction.objects.filter(
        investigated=False
    ).count()

    # Méthodes de paiement
    payment_methods = PaymentMethod.objects.count()
    active_methods = PaymentMethod.objects.filter(user__is_active=True).count()

    # Activité récente
    recent_activities = []

    # Transactions récentes
    recent_transactions = Transaction.objects.filter(
        created_at__gte=now - timedelta(hours=24)
    ).order_by("-created_at")[:5]

    for transaction in recent_transactions:
        activity_type = "success" if transaction.status == "succeeded" else "warning"
        if transaction.status == "failed":
            activity_type = "danger"

        recent_activities.append(
            {
                "type": activity_type,
                "icon": "💳",
                "title": f"Transaction {transaction.status}",
                "description": f'{transaction.amount} {transaction.currency} - {transaction.user.username if transaction.user else "Anonyme"}',
                "timestamp": transaction.created_at,
            }
        )

    # Webhooks récents
    recent_webhooks = WebhookLog.objects.filter(
        received_at__gte=now - timedelta(hours=24)
    ).order_by("-received_at")[:5]

    for webhook in recent_webhooks:
        activity_type = "success" if webhook.processed_successfully else "danger"

        recent_activities.append(
            {
                "type": activity_type,
                "icon": "📡",
                "title": f"Webhook {webhook.provider}",
                "description": f'{webhook.event_type} - {"Traité" if webhook.processed_successfully else "Échec"}',
                "timestamp": webhook.received_at,
            }
        )

    # Transactions orphelines récentes
    recent_orphans = OrphanTransaction.objects.filter(
        webhook_received_at__gte=now - timedelta(hours=24)
    ).order_by("-webhook_received_at")[:3]

    for orphan in recent_orphans:
        recent_activities.append(
            {
                "type": "warning",
                "icon": "⚠️",
                "title": "Transaction orpheline détectée",
                "description": f"{orphan.provider} - {orphan.amount} {orphan.currency}",
                "timestamp": orphan.webhook_received_at,
            }
        )

    # Trier les activités par timestamp
    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)
    recent_activities = recent_activities[:10]  # Garder seulement les 10 plus récentes

    # Statut des webhooks
    recent_webhook_failures = WebhookLog.objects.filter(
        processed_successfully=False, received_at__gte=now - timedelta(hours=1)
    ).count()

    if recent_webhook_failures > 5:
        webhook_status = "warning"
        webhook_status_text = f"{recent_webhook_failures} échecs récents"
    elif recent_webhook_failures > 0:
        webhook_status = "warning"
        webhook_status_text = f"{recent_webhook_failures} échec(s) récent(s)"
    else:
        webhook_status = "online"
        webhook_status_text = "Tous les webhooks traités"

    # Contexte pour le template
    context = {
        "title": "Dashboard Paiements",
        "current_time": now,
        "stats": {
            "total_transactions": total_transactions,
            "successful_transactions": successful_transactions,
            "total_webhooks": total_webhooks,
            "webhook_success_rate": webhook_success_rate,
            "orphan_transactions": orphan_transactions,
            "uninvestigated_orphans": uninvestigated_orphans,
            "payment_methods": payment_methods,
            "active_methods": active_methods,
        },
        "recent_activities": recent_activities,
        "webhook_status": webhook_status,
        "webhook_status_text": webhook_status_text,
    }

    return render(request, "admin/payments_dashboard.html", context)


@staff_member_required
def webhook_analytics(request):
    """Vue d'analyse des webhooks"""

    # Analyse par fournisseur
    webhook_by_provider = WebhookLog.objects.values("provider").annotate(
        total=Count("id"),
        successful=Count("id", filter=Q(processed_successfully=True)),
        failed=Count("id", filter=Q(processed_successfully=False)),
    )

    # Analyse par type d'événement
    webhook_by_event = (
        WebhookLog.objects.values("event_type")
        .annotate(
            total=Count("id"),
            successful=Count("id", filter=Q(processed_successfully=True)),
        )
        .order_by("-total")[:10]
    )

    # Analyse temporelle (derniers 7 jours)
    seven_days_ago = timezone.now() - timedelta(days=7)
    daily_webhooks = []

    for i in range(7):
        day = seven_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        count = WebhookLog.objects.filter(
            received_at__gte=day_start, received_at__lt=day_end
        ).count()

        daily_webhooks.append({"date": day_start.strftime("%d/%m"), "count": count})

    context = {
        "title": "Analyse des Webhooks",
        "webhook_by_provider": webhook_by_provider,
        "webhook_by_event": webhook_by_event,
        "daily_webhooks": daily_webhooks,
    }

    return render(request, "admin/webhook_analytics.html", context)


@staff_member_required
def transaction_analytics(request):
    """Vue d'analyse des transactions"""

    # Analyse par statut
    transaction_by_status = Transaction.objects.values("status").annotate(
        total=Count("id"), total_amount=Sum("amount")
    )

    # Analyse par fournisseur
    transaction_by_provider = Transaction.objects.values("provider").annotate(
        total=Count("id"),
        total_amount=Sum("amount"),
        avg_amount=Sum("amount") / Count("id"),
    )

    # Tendances (derniers 30 jours)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_transactions = []

    for i in range(30):
        day = thirty_days_ago + timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        count = Transaction.objects.filter(
            created_at__gte=day_start, created_at__lt=day_end
        ).count()

        amount = (
            Transaction.objects.filter(
                created_at__gte=day_start, created_at__lt=day_end, status="succeeded"
            ).aggregate(total=Sum("amount"))["total"]
            or 0
        )

        daily_transactions.append(
            {
                "date": day_start.strftime("%d/%m"),
                "count": count,
                "amount": float(amount),
            }
        )

    context = {
        "title": "Analyse des Transactions",
        "transaction_by_status": transaction_by_status,
        "transaction_by_provider": transaction_by_provider,
        "daily_transactions": daily_transactions,
    }

    return render(request, "admin/transaction_analytics.html", context)
