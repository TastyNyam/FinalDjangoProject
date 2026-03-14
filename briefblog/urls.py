from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    path('', views.post_list, name='post_list'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new/', views.create_post, name='create_post'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),
    path('profile/<str:username>/', views.profile_view, name='profile'),
    path('about/', TemplateView.as_view(template_name="about.html"), name='about'),
    path('privacy/', TemplateView.as_view(template_name="privacy.html"), name='privacy'),
    path('comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
    path('comment/<int:pk>/edit/', views.comment_edit, name='comment_edit'),
    path('settings/', views.edit_settings, name='settings'),
    path('notifications/', views.notifications_view, name='notifications'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)