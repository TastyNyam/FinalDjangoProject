# briefblog/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    # Профиль создаем ТОЛЬКО если пользователь был только что создан
    if created:
        # Используем get_or_create на случай, если профиль уже
        # успел создаться каким-то другим образом
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Проверяем наличие профиля перед сохранением, чтобы не упасть в ошибку
    if hasattr(instance, 'profile'):
        instance.profile.save()