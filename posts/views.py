from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, DeleteView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.urls import reverse_lazy
from django.utils import timezone
from .models import Post, Like, Comment, Story, StoryView, StoryArchive, Notification
from .forms import PostForm, CommentForm, StoryForm
from accounts.models import User, Follow, FollowRequestNotification


class FeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'posts/feed.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        following_users = self.request.user.following.values_list('following', flat=True)
        return Post.objects.filter(
            Q(author__in=following_users) | Q(author=self.request.user)
        ).select_related('author').prefetch_related('likes', 'comments__author')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Archive expired stories
        self.archive_expired_stories()
        
        # Get active stories from followed users
        following_users = self.request.user.following.values_list('following', flat=True)
        following_users = list(following_users) + [self.request.user.id]
        
        stories = Story.objects.filter(
            author__in=following_users,
            is_archived=False
        ).exclude(
            expires_at__lt=timezone.now()
        ).order_by('-created_at')
        
        # Group stories by author
        stories_by_author = {}
        for story in stories:
            if story.author.id not in stories_by_author:
                stories_by_author[story.author.id] = {
                    'author': story.author,
                    'stories': [],
                    'latest_story': story
                }
            stories_by_author[story.author.id]['stories'].append(story)
            if story.created_at > stories_by_author[story.author.id]['latest_story'].created_at:
                stories_by_author[story.author.id]['latest_story'] = story
        
        context['stories_by_author'] = stories_by_author.values()
        context['has_stories'] = len(stories_by_author) > 0
        
        # Get follow request notifications
        follow_requests_count = FollowRequestNotification.objects.filter(
            user=self.request.user,
            is_read=False
        ).count()
        context['follow_requests_count'] = follow_requests_count
        
        return context
    
    def archive_expired_stories(self):
        """Archive expired stories"""
        
        expired_stories = Story.objects.filter(
            expires_at__lt=timezone.now(),
            is_archived=False
        )
        
        for story in expired_stories:
            # Create archive entry
            StoryArchive.objects.create(
                author=story.author,
                image=story.image,
                caption=story.caption,
                original_created_at=story.created_at,
                views_count=story.views_count
            )
            
            # Mark story as archived
            story.is_archived = True
            story.save()


class PostDetailView(LoginRequiredMixin, DetailView):
    model = Post
    template_name = 'posts/post_detail.html'
    context_object_name = 'post'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['is_liked'] = Like.objects.filter(
            user=self.request.user, 
            post=self.get_object()
        ).exists()
        return context


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post created successfully!')
            return redirect('posts:feed')
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'posts/delete_post.html'
    success_url = reverse_lazy('posts:feed')
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)


@login_required
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if created:
        post.likes_count += 1
        post.save()
        is_liked = True
    else:
        like.delete()
        post.likes_count -= 1
        post.save()
        is_liked = False
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'is_liked': is_liked,
            'likes_count': post.likes_count
        })
    
    return redirect('posts:post_detail', pk=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = request.user
            comment.post = post
            comment.save()
            post.comments_count += 1
            post.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'comment_id': comment.id,
                    'author': comment.author.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                    'author_avatar': comment.author.profile_picture.url if comment.author.profile_picture else '/static/images/default-avatar.png'
                })
    
    return redirect('posts:post_detail', pk=post_id)


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    post = comment.post
    comment.delete()
    post.comments_count -= 1
    post.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('posts:post_detail', pk=post.pk)


class ExploreView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'posts/explore.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        query = self.request.GET.get('q', '')
        # Get users that the current user follows
        following_users = self.request.user.following.values_list('following', flat=True)
        
        if query:
            # For search, include posts from followed users (including private) and public users
            return Post.objects.filter(
                (Q(caption__icontains=query) |
                Q(author__username__icontains=query)) &
                (Q(author__is_private=False) | Q(author_id__in=following_users))
            ).select_related('author').prefetch_related('likes', 'comments__author').order_by('-created_at')
        else:
            # For explore, only show posts from public users or followed users
            return Post.objects.filter(
                Q(author__is_private=False) | Q(author_id__in=following_users)
            ).select_related('author').prefetch_related('likes', 'comments__author').order_by('?')[:100]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class UserPostsView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'posts/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        username = self.kwargs.get('username')
        return Post.objects.filter(author__username=username).select_related('author')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username = self.kwargs.get('username')
        from django.contrib.auth import get_user_model
        User = get_user_model()
        context['profile_user'] = get_object_or_404(User, username=username)
        return context


@login_required
def search(request):
    query = request.GET.get('q', '')
    users = []
    
    if query:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Search users only
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
    
    return render(request, 'posts/search.html', {'users': users, 'query': query})


class NotificationView(LoginRequiredMixin, ListView):
    model = None  # Will be defined when notifications model is created
    template_name = 'posts/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        # Get regular notifications
        notifications = Notification.objects.filter(
            recipient=self.request.user
        ).select_related('sender', 'post', 'comment').order_by('-created_at')
        
        # Get follow request notifications
        follow_requests = FollowRequestNotification.objects.filter(
            user=self.request.user
        ).select_related('follow_request__from_user').order_by('-created_at')
        
        # Combine both types of notifications
        combined_notifications = []
        
        # Add regular notifications
        for notification in notifications:
            combined_notifications.append({
                'id': f"notif_{notification.id}",
                'type': 'notification',
                'actor': notification.sender.username,
                'actor_avatar': notification.sender.profile_picture.url if notification.sender.profile_picture else '/static/images/default-avatar.png',
                'verb': self.get_notification_verb(notification),
                'target': self.get_notification_target(notification),
                'time_ago': self.get_time_ago(notification.created_at),
                'is_read': notification.is_read,
                'notification_obj': notification
            })
        
        # Add follow request notifications
        for follow_req_notification in follow_requests:
            combined_notifications.append({
                'id': f"follow_req_{follow_req_notification.id}",
                'type': 'follow_request',
                'actor': follow_req_notification.follow_request.from_user.username,
                'actor_avatar': follow_req_notification.follow_request.from_user.profile_picture.url if follow_req_notification.follow_request.from_user.profile_picture else '/static/images/default-avatar.png',
                'verb': 'requested to follow you',
                'target': '',
                'time_ago': self.get_time_ago(follow_req_notification.created_at),
                'is_read': follow_req_notification.is_read,
                'follow_request_id': follow_req_notification.follow_request.id
            })
        
        # Sort by creation time
        combined_notifications.sort(key=lambda x: x['time_ago'], reverse=True)
        return combined_notifications
    
    def get_notification_verb(self, notification):
        if notification.notification_type == 'like':
            return 'liked your post'
        elif notification.notification_type == 'comment':
            return 'commented on your post'
        elif notification.notification_type == 'follow':
            return 'started following you'
        else:
            return 'interacted with you'
    
    def get_notification_target(self, notification):
        if notification.post:
            return f"your post"
        elif notification.comment:
            return f"your comment"
        return ''
    
    def get_time_ago(self, created_at):
        from django.utils import timezone
        now = timezone.now()
        diff = now - created_at
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"


@login_required
def mark_notifications_read(request):
    # Placeholder - will implement when notifications model is created
    return JsonResponse({'success': True})


@login_required
def mark_notification_read(request, notification_id):
    # Placeholder - will implement when notifications model is created
    return JsonResponse({'success': True})


@login_required
def unread_notification_count(request):
    # Count unread regular notifications
    regular_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    # Count unread follow request notifications
    follow_request_notifications = FollowRequestNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    total_count = regular_notifications + follow_request_notifications
    return JsonResponse({'count': total_count})


@login_required
def popular_accounts(request):
    """API endpoint to get popular accounts based on followers count"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get users with most followers (excluding current user and users already followed)
    following_users = request.user.following.values_list('following', flat=True)
    following_users = list(following_users) + [request.user.id]
    
    popular_users = User.objects.exclude(id__in=following_users).order_by('-followers_count')[:5]
    
    users_data = []
    for user in popular_users:
        users_data.append({
            'username': user.username,
            'bio': user.bio if user.bio else '',
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'followers_count': user.followers_count
        })
    
    return JsonResponse({'users': users_data})


@login_required
def suggested_accounts(request):
    """API endpoint to get suggested accounts"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Get users that current user doesn't follow (excluding self)
    following_users = request.user.following.values_list('following', flat=True)
    following_users = list(following_users) + [request.user.id]
    
    # Get random suggestions
    import random
    suggested_users = User.objects.exclude(id__in=following_users).order_by('?')[:5]
    
    users_data = []
    for user in suggested_users:
        users_data.append({
            'username': user.username,
            'bio': user.bio if user.bio else '',
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'followers_count': user.followers_count
        })
    
    return JsonResponse({'users': users_data})


@login_required
def create_story(request):
    if request.method == 'POST':
        form = StoryForm(request.POST, request.FILES)
        if form.is_valid():
            story = form.save(commit=False)
            story.author = request.user
            
            # Handle text overlay data
            caption_data = request.POST.get('caption', '')
            if caption_data:
                try:
                    import json
                    text_data = json.loads(caption_data)
                    # Store the complete text overlay data as JSON
                    story.caption = caption_data
                except json.JSONDecodeError:
                    # Fallback to regular caption if JSON parsing fails
                    story.caption = caption_data
            
            story.save()
            messages.success(request, 'Story created successfully!')
            return redirect('posts:feed')
    else:
        form = StoryForm()
    
    return render(request, 'posts/create_story.html', {'form': form})


@login_required
def story_detail(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    
    # Check if story is expired
    if story.is_expired():
        messages.error(request, 'This story has expired.')
        return redirect('posts:feed')
    
    # Check privacy settings
    if story.author.is_private and story.author != request.user:
        if not Follow.objects.filter(follower=request.user, following=story.author).exists():
            messages.error(request, 'This story is private.')
            return redirect('posts:feed')
    
    # Record story view
    story_view, created = StoryView.objects.get_or_create(
        story=story,
        viewer=request.user
    )
    
    if created:
        story.views_count += 1
        story.save()
    
    # Get other stories from the same author
    other_stories = Story.objects.filter(
        author=story.author,
        is_archived=False
    ).exclude(id=story_id).order_by('-created_at')
    
    return render(request, 'posts/story_detail.html', {
        'story': story,
        'other_stories': other_stories
    })


@login_required
def archive_expired_stories():
    """Archive all expired stories - this would typically be called by a cron job"""
    from django.utils import timezone
    
    expired_stories = Story.objects.filter(
        expires_at__lt=timezone.now(),
        is_archived=False
    )
    
    for story in expired_stories:
        # Create archive entry
        StoryArchive.objects.create(
            author=story.author,
            image=story.image,
            caption=story.caption,
            original_created_at=story.created_at,
            views_count=story.views_count
        )
        
        # Mark story as archived
        story.is_archived = True
        story.save()
    
    return f"Archived {expired_stories.count()} stories"
