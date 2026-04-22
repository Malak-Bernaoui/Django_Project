from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    username = models.CharField(max_length=30, unique=True)
    real_name = models.CharField(max_length=100, blank=True, help_text="Your real name (optional)")
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg')
    website = models.URLField(max_length=200, blank=True, help_text="Your personal website or portfolio")
    is_private = models.BooleanField(default=False, help_text="Make your account private")
    followers_count = models.PositiveIntegerField(default=0)
    following_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.username


class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f'{self.follower} follows {self.following}'


class FollowRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='follow_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='follow_requests_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ], default='pending')
    
    class Meta:
        unique_together = ('from_user', 'to_user')
    
    def __str__(self):
        return f'{self.from_user} requested to follow {self.to_user} ({self.status})'


class FollowRequestNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_user')
    follow_request = models.ForeignKey(FollowRequest, on_delete=models.CASCADE)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Follow request from {self.follow_request.from_user.username}'
