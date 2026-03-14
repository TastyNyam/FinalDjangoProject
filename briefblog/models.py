from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name="Заголовок")
    body = models.TextField(verbose_name="Текст поста")
    cover = models.ImageField(upload_to='covers/', blank=True, null=True,)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # НОВОЕ ПОЛЕ:
    # 'self' означает связь с этой же моделью.
    # null=True, так как у обычных комментариев нет родителя.
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    # Добавляем это:
    reply_to = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f'{self.author.username}: {self.text[:20]}'

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'user')  # один лайк на пользователя


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    display_name = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)

    # НОВОЕ: когда в последний раз меняли системный логин
    last_username_change = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

# Эти функции (сигналы) будут автоматически создавать профиль,
# когда регистрируется новый пользователь
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # При создании профиля записываем username в публичное имя
        Profile.objects.create(user=instance, display_name=instance.username)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Notification(models.Model):
    # Типы уведомлений
    TYPE_CHOICES = (
        ('like', 'Лайк'),
        ('comment', 'Комментарий'),
        ('reply', 'Ответ'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
