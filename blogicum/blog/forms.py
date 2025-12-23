from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Post, Category, Location, Comment

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        #exclude = ('title', 'text', 'pub_date', 'location', 'category', 'image', 'is_published')
        exclude = ('author', 'created_at')
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%d %H:%M:%S',
                attrs={'type': 'datetime-local'}
            ),
            'text': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if 'author' in self.fields:
            del self.fields['author']
        
        if 'category' in self.fields:
            self.fields['category'].queryset = Category.objects.filter(is_published=True)
        
        if 'location' in self.fields:
            self.fields['location'].queryset = Location.objects.filter(is_published=True)
    
    def save(self, commit=True):
        post = super().save(commit=False)
        if self.user:
            post.author = self.user
        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Оставьте комментарий...'})
        }