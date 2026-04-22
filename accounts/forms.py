from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'real_name', 'email', 'bio', 'website', 'profile_picture', 'is_private')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'real_name': forms.TextInput(attrs={'placeholder': 'Your real name'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://yourwebsite.com'}),
            'username': forms.TextInput(attrs={'placeholder': 'Choose a unique username'}),
        }
        labels = {
            'real_name': 'Real Name',
            'website': 'Website',
            'is_private': 'Private Account',
            'bio': 'Bio',
            'profile_picture': 'Profile Picture',
        }
        help_texts = {
            'real_name': 'This will be displayed on your profile',
            'website': 'Link to your personal website or portfolio',
            'is_private': 'Only approved followers can see your posts',
        }
