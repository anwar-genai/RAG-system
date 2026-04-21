from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # First user on the system is promoted to admin. All later users default to 'user'.
        has_admin = UserProfile.objects.filter(role='admin').exists()
        UserProfile.objects.get_or_create(
            user=instance,
            defaults={'role': 'user' if has_admin else 'admin'},
        )
