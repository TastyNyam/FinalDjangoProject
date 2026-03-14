from django.http import HttpResponse
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from .forms import *
import random, string
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Добро пожаловать, @{user.username}!")
            return redirect('post_list')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def post_list(request):
    query = request.GET.get('q')

    if query:
        query = query.strip()
        posts = Post.objects.filter(
            (Q(title__icontains=query) | Q(body__icontains=query)) |
            (Q(title__icontains=query.lower()) | Q(body__icontains=query.lower())) |
            (Q(title__icontains=query.capitalize()) | Q(body__icontains=query.capitalize())),
            is_published=True
        ).distinct().order_by('-created_at')
    else:
        posts = Post.objects.filter(is_published=True).order_by('-created_at')

    # после того как получаем posts
    for post in posts:
        post.is_liked = Like.objects.filter(post=post, user=request.user).exists()

    return render(request, 'post_list.html', {'posts': posts, 'query': query})

@login_required
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    is_liked = Like.objects.filter(post=post, user=request.user).exists()

    if request.method == 'POST':
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user

            # Логика ответов (у тебя она уже есть)
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent = Comment.objects.get(id=parent_id)
                reply_to_user = request.POST.get('reply_to_user')
                if reply_to_user:
                    comment.reply_to = reply_to_user

            comment.save()

            # --- НОВАЯ ЛОГИКА УВЕДОМЛЕНИЙ ТУТ ---

            # 1. Уведомление автору поста (если комментирует не сам автор)
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    post=post,
                    notification_type='comment',
                    text=comment.text[:50]  # Сохраняем начало текста для превью
                )

            # 2. Уведомление автору родительского комментария (если это ответ)
            if comment.parent and comment.parent.author != request.user:
                # Проверяем, чтобы не отправить два уведомления одному человеку
                # (если автор поста и автор комментария — одно лицо, ему хватит одного)
                if comment.parent.author != post.author:
                    Notification.objects.create(
                        recipient=comment.parent.author,
                        sender=request.user,
                        post=post,
                        notification_type='reply',
                        text=comment.text[:50]
                    )

            # --- ДОБАВЛЯЕМ ЛОГИКУ ДЛЯ AJAX ---
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'comment_id': comment.id,
                    'text': comment.text,
                    'author': comment.author.username,
                    'display_name': comment.author.profile.display_name or comment.author.username,
                    'avatar_url': comment.author.profile.avatar.url if comment.author.profile.avatar else None,
                    'parent_id': parent_id,
                    'reply_to': comment.reply_to,
                    'created_at': "Только что"
                })
            # ---------------------------------

            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()

    # Получаем только основные комментарии (те, у которых нет родителя)
    main_comments = post.comments.filter(parent__isnull=True).order_by('-created_at')

    return render(request, 'post_detail.html', {
        'post': post,
        'form': form,
        'is_liked': is_liked,
        'main_comments': main_comments
    })

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Запись создана!")
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})


@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    like, created = Like.objects.get_or_create(post=post, user=request.user)

    if created:
        liked = True
        # СОЗДАЕМ УВЕДОМЛЕНИЕ (если лайкнул не свой пост)
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                post=post,
                notification_type='like'
            )
    else:
        # Если лайк убирают, можно найти и удалить уведомление,
        # но обычно их оставляют или просто не заморачиваются.
        like.delete()
        liked = False

    return JsonResponse({
        'likes_count': post.likes.count(),
        'liked': liked  # Передаем точный статус обратно в браузер
    })

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        messages.error(request, "Доступ запрещен")
        return redirect('post_detail', pk=pk)

    if request.method == "POST":
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Изменения сохранены")
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'create_post.html', {'form': form, 'edit_mode': True})

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
        post.delete()
        messages.warning(request, "Запись удалена")
    return redirect('post_list')


from django.db.models import Count, Sum


def profile_view(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user_profile, is_published=True).order_by('-created_at')

    # Проверяем, лайкнут ли каждый пост текущим пользователем
    for post in posts:
        post.is_liked = Like.objects.filter(post=post, user=request.user).exists()

    total_likes = Like.objects.filter(post__author=user_profile).count()

    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'posts': posts,
        'total_likes': total_likes
    })


@login_required
def comment_delete(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk

    # Удалить может либо автор комментария, либо владелец поста
    if request.user == comment.author or request.user == comment.post.author:
        comment.delete()
        messages.warning(request, "Комментарий удален")
    else:
        messages.error(request, "У вас нет прав на это действие")

    return redirect('post_detail', pk=post_pk)


@login_required
def comment_edit(request, pk):
    comment = get_object_or_404(Comment, pk=pk)

    # Редактировать может только автор комментария
    if request.user != comment.author:
        messages.error(request, "Вы не можете редактировать чужой комментарий")
        return redirect('post_detail', pk=comment.post.pk)

    if request.method == "POST":
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, "Комментарий обновлен")
            return redirect('post_detail', pk=comment.post.pk)
    else:
        form = CommentForm(instance=comment)

    # Чтобы не плодить шаблоны, передаем данные для редактирования в ту же страницу поста
    post = comment.post
    main_comments = post.comments.filter(parent__isnull=True).order_by('-created_at')
    is_liked = Like.objects.filter(post=post, user=request.user).exists()

    return render(request, 'post_detail.html', {
        'post': post,
        'form': form,  # Здесь будет форма с текстом комментария
        'edit_mode': True,
        'edit_comment': comment,
        'is_liked': is_liked,
        'main_comments': main_comments
    })


from django.utils import timezone
from datetime import timedelta
import base64
from django.core.files.base import ContentFile


@login_required
def edit_settings(request):
    # 1. Гарантируем наличие профиля
    profile, created = Profile.objects.get_or_create(user=request.user)

    if created:
        profile.display_name = request.user.username
        profile.save()

    # 2. Логика кулдауна (14 дней)
    can_change_username = True
    cooldown_days = 14
    days_left = 0

    if profile.last_username_change:
        time_diff = timezone.now() - profile.last_username_change
        if time_diff < timedelta(days=cooldown_days):
            can_change_username = False
            days_left = cooldown_days - time_diff.days


    # 3. Обработка сохранения (POST)
    if request.method == 'POST':
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        # Логика удаления аватара
        if request.POST.get('delete_avatar') == "true":
            profile.avatar.delete()  # Удаляет сам файл
            profile.avatar = None  # Убирает ссылку в базе
            profile.save()

        # Обработка кропа (аватарки)
        cropped_data = request.POST.get('cropped_avatar')
        if cropped_data:
            format, imgstr = cropped_data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'{request.user.username}_avatar.{ext}')
            profile.avatar = data
            # Сохраняем сразу, чтобы p_form не перезаписала старым файлом
            profile.save()

        if p_form.is_valid():
            # Обработка смены системного Username
            new_username = request.POST.get('username')
            if new_username and new_username != request.user.username:
                if can_change_username:
                    if User.objects.filter(username=new_username).exists():
                        messages.error(request, "Этот логин уже занят.")
                    else:
                        request.user.username = new_username
                        request.user.save()
                        profile.last_username_change = timezone.now()
                        profile.save()
                        messages.success(request, "Логин изменен!")
                else:
                    messages.error(request, f"Менять логин можно раз в 14 дней. Жди еще {days_left} дн.")

            p_form.save()
            messages.success(request, "Настройки профиля обновлены!")
            # Перенаправляем на профиль с НОВЫМ (или старым) именем
            return redirect('profile', username=request.user.username)
    else:
        p_form = ProfileUpdateForm(instance=profile)

    return render(request, 'settings.html', {
        'p_form': p_form,
        'can_change_username': can_change_username,
        'days_left': days_left
    })


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    # Помечаем все как прочитанные при просмотре
    unread = notifications.filter(is_read=False)
    unread.update(is_read=True)

    return render(request, 'notifications.html', {'notifications': notifications})