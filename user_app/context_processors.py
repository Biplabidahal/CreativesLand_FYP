from datetime import timedelta
from django.utils import timezone
from .models import BlogComment, Payment

def notifications(request):
    if request.user.is_authenticated:
        # Define a timeframe for what is considered "new" (e.g. last 1 day)
        time_threshold = timezone.now() - timedelta(days=1)

        # New comments on blogs where the user is the author (exclude self-comments)
        notifications_comments = BlogComment.objects.filter(
            blog__author=request.user,
            created_at__gte=time_threshold
        ).exclude(user=request.user)

        # New purchases on blogs where the user is the author
        notifications_purchases = Payment.objects.filter(
            blog__author=request.user,
            payment_status='completed',
            created_at__gte=time_threshold
        )

        notifications_total = notifications_comments.count() + notifications_purchases.count()
        return {
            "notifications_comments": notifications_comments,
            "notifications_purchases": notifications_purchases,
            "notifications_total": notifications_total,
        }
    return {}
