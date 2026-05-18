from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, DeleteView, TemplateView
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
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
@require_POST
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    
    if created:
        post.likes_count += 1
        post.save()
        is_liked = True
        if post.author_id != request.user.id:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                notification_type='like',
                post=post,
            )
    else:
        like.delete()
        post.likes_count = max(0, post.likes_count - 1)
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
            if post.author_id != request.user.id:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post=post,
                    comment=comment,
                )
            
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
            # For explore, only show posts from public users or followed users (not own posts)
            return Post.objects.filter(
                Q(author__is_private=False) | Q(author_id__in=following_users)
            ).exclude(
                author=self.request.user
            ).select_related('author').prefetch_related('likes', 'comments__author').order_by('?')[:100]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        page_posts = context.get('object_list', [])
        explore_items = []
        for post in page_posts:
            explore_items.append({
                'type': 'post',
                'id': post.id,
                'image_url': post.image.url,
                'likes_count': post.likes_count,
                'comments_count': post.comments_count,
                'detail_url': reverse('posts:post_detail', args=[post.id]),
            })
        # Add placeholder images alongside database posts (uniform grid sizing in template)
        filler_start = len(explore_items)
        filler_count = max(12, 24 - len(explore_items))
        for i in range(filler_count):
            seed = f'explore{self.request.user.id}{filler_start + i}'
            explore_items.append({
                'type': 'placeholder',
                'image_url': f'https://picsum.photos/seed/{seed}/400/400',
                'likes_count': (i % 50) + 10,
                'comments_count': (i % 20) + 1,
                'detail_url': None,
            })
        context['explore_items'] = explore_items
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
    query = request.GET.get('q', '').strip()
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

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        following_ids = set(
            request.user.following.values_list('following_id', flat=True)
        )
        users_data = []
        for user in users:
            users_data.append({
                'username': user.username,
                'bio': user.bio or '',
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'is_private': user.is_private,
                'followers_count': user.followers_count,
                'profile_url': reverse('accounts:profile', args=[user.username]),
                'is_following': user.id in following_ids,
            })
        return JsonResponse({'users': users_data, 'query': query})
    
    return render(request, 'posts/search.html', {'users': users, 'query': query})


@login_required
def share_post_followers(request, post_id):
    """List followers the current user can share a post with."""
    get_object_or_404(Post, id=post_id)
    follower_ids = Follow.objects.filter(
        following=request.user
    ).values_list('follower_id', flat=True)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    followers = User.objects.filter(id__in=follower_ids).order_by('username')[:50]
    followers_data = []
    for user in followers:
        followers_data.append({
            'id': user.id,
            'username': user.username,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
        })
    return JsonResponse({'followers': followers_data})


@login_required
@require_POST
def share_post(request, post_id):
    """Share a post with the user's followers via notifications."""
    post = get_object_or_404(Post, id=post_id)
    follower_ids = Follow.objects.filter(
        following=request.user
    ).values_list('follower_id', flat=True)
    from django.contrib.auth import get_user_model
    User = get_user_model()
    recipients = User.objects.filter(id__in=follower_ids)
    shared_count = 0
    for recipient in recipients:
        Notification.objects.create(
            recipient=recipient,
            sender=request.user,
            notification_type='share',
            post=post,
        )
        shared_count += 1
    return JsonResponse({
        'success': True,
        'shared_count': shared_count,
        'message': f'Post shared with {shared_count} follower(s).',
    })


def get_time_ago(created_at):
    from django.utils import timezone
    now = timezone.now()
    diff = now - created_at
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    if diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    if diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    return 'just now'


def get_notification_verb(notification):
    verbs = {
        'like': 'liked your post',
        'comment': 'commented on your post',
        'follow': 'started following you',
        'share': 'shared a post with you',
    }
    return verbs.get(notification.notification_type, 'interacted with you')


def get_notification_target(notification):
    if notification.post:
        return 'your post'
    if notification.comment:
        return 'your comment'
    return ''


def build_notifications_list(user):
    combined = []
    notifications = Notification.objects.filter(
        recipient=user
    ).select_related('sender', 'post', 'comment').order_by('-created_at')
    for notification in notifications:
        combined.append({
            'id': f'notif_{notification.id}',
            'type': 'notification',
            'actor': notification.sender.username,
            'actor_profile_url': reverse('accounts:profile', args=[notification.sender.username]),
            'actor_avatar': notification.sender.profile_picture.url if notification.sender.profile_picture else '/static/images/default-avatar.png',
            'verb': get_notification_verb(notification),
            'target': get_notification_target(notification),
            'time_ago': get_time_ago(notification.created_at),
            'is_read': notification.is_read,
            'post_url': reverse('posts:post_detail', args=[notification.post_id]) if notification.post_id else None,
            'sort_key': notification.created_at.timestamp(),
        })
    follow_requests = FollowRequestNotification.objects.filter(
        user=user,
        follow_request__status='pending',
    ).select_related('follow_request__from_user').order_by('-created_at')
    for follow_req_notification in follow_requests:
        combined.append({
            'id': f'follow_req_{follow_req_notification.id}',
            'type': 'follow_request',
            'actor': follow_req_notification.follow_request.from_user.username,
            'actor_profile_url': reverse('accounts:profile', args=[follow_req_notification.follow_request.from_user.username]),
            'actor_avatar': follow_req_notification.follow_request.from_user.profile_picture.url if follow_req_notification.follow_request.from_user.profile_picture else '/static/images/default-avatar.png',
            'verb': 'requested to follow you',
            'target': '',
            'time_ago': get_time_ago(follow_req_notification.created_at),
            'is_read': follow_req_notification.is_read,
            'follow_request_id': follow_req_notification.follow_request.id,
            'post_url': None,
            'sort_key': follow_req_notification.created_at.timestamp(),
        })
    combined.sort(key=lambda item: item['sort_key'], reverse=True)
    return combined


class NotificationView(LoginRequiredMixin, TemplateView):
    template_name = 'posts/notifications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notifications'] = build_notifications_list(self.request.user)
        return context

    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'notifications': build_notifications_list(request.user),
            })
        return super().get(request, *args, **kwargs)


@login_required
@require_POST
def mark_notifications_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    FollowRequestNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    if notification_id.startswith('notif_'):
        pk = int(notification_id.replace('notif_', ''))
        Notification.objects.filter(id=pk, recipient=request.user).update(is_read=True)
    elif notification_id.startswith('follow_req_'):
        pk = int(notification_id.replace('follow_req_', ''))
        FollowRequestNotification.objects.filter(id=pk, user=request.user).update(is_read=True)
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
