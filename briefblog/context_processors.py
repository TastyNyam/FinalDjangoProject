from .models import Notification


def notifications_context(request):
    if request.user.is_authenticated:
        # Получаем только непрочитанные для счетчика
        unread_notifications_count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        # Получаем последние 5 уведомлений для быстрого просмотра (опционально)
        recent_notifications = Notification.objects.filter(
            recipient=request.user
        ).order_by('-created_at')[:5]

        return {
            'unread_count': unread_notifications_count,
            'recent_notifications': recent_notifications
        }
    return {}