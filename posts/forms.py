from django import forms
from .models import Post, Comment, Story


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('image', 'caption')
        widgets = {
            'caption': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write a caption...'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add a comment...'}),
        }


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ('image', 'caption')
        widgets = {
            'caption': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add a caption for your story...'}),
        }
        labels = {
            'image': 'Story Image',
            'caption': 'Caption (optional)'
        }
