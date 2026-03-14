from django import forms
from .models import *

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']  # пользователь вводит только текст комментария
        widgets = {
            'text': forms.Textarea(attrs={'rows':3, 'cols':40, 'placeholder':'Write a comment...'}),
        }

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body', 'cover']
        widgets = {
            # Заменяем обычный ввод на текстовую область для авто-расширения
            'title': forms.Textarea(attrs={
                'rows': 1,
                'placeholder': 'Введите заголовок...',
                'style': 'font-weight: 700; font-size: 24px;' # Делаем заголовок жирным сразу при вводе
            }),
            'body': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'О чем вы хотите рассказать?'
            }),
        }

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'avatar', 'bio']