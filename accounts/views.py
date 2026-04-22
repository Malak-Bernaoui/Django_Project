from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.db.models import Count
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import User, Follow, FollowRequest, FollowRequestNotification
from .forms import CustomUserCreationForm, UserUpdateForm


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return '/feed/'


class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        messages.success(request, 'You have been logged out successfully.')
        # Add headers to prevent frame issues
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    
    def get_next_page(self):
        return '/accounts/login/'


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully!')
            return redirect('posts:feed')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.get_object()
        
        # Check if following
        context['is_following'] = Follow.objects.filter(
            follower=self.request.user, 
            following=profile_user
        ).exists()
        
        # Check if there's a pending follow request
        context['has_pending_request'] = FollowRequest.objects.filter(
            from_user=self.request.user,
            to_user=profile_user,
            status='pending'
        ).exists()
        
        # Get followers and following lists
        context['followers_list'] = Follow.objects.filter(following=profile_user).select_related('follower')
        context['following_list'] = Follow.objects.filter(follower=profile_user).select_related('following')
        
        # Get pending follow requests for the profile owner
        if profile_user == self.request.user:
            context['pending_requests'] = FollowRequest.objects.filter(
                to_user=profile_user,
                status='pending'
            ).select_related('from_user').order_by('-created_at')
            context['pending_requests_count'] = context['pending_requests'].count()
        else:
            context['pending_requests'] = []
            context['pending_requests_count'] = 0
        
        return context


@login_required
def edit_profile(request, username):
    # Security check: users can only edit their own profile
    if request.user.username != username:
        messages.error(request, "You can only edit your own profile.")
        return redirect('accounts:profile', username=request.user.username)
    
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile', username=request.user.username)
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow != request.user:
        # Check if already following
        existing_follow = Follow.objects.filter(
            follower=request.user,
            following=user_to_follow
        ).first()
        
        if existing_follow:
            # Already following
            message = "You are already following this user."
            followed = False
        else:
            # Check if there's already a pending request
            existing_request = FollowRequest.objects.filter(
                from_user=request.user,
                to_user=user_to_follow,
                status='pending'
            ).first()
            
            if existing_request:
                # Request already sent
                message = "Follow request already sent."
                followed = False
            elif user_to_follow.is_private:
                # Private account - create follow request
                follow_request, created = FollowRequest.objects.get_or_create(
                    from_user=request.user,
                    to_user=user_to_follow,
                    defaults={'status': 'pending'}
                )
                if created:
                    # Create notification for the user
                    FollowRequestNotification.objects.create(
                        user=user_to_follow,
                        follow_request=follow_request
                    )
                    message = "Follow request sent!"
                    followed = False
                else:
                    message = "Follow request already sent."
                    followed = False
            else:
                # Public account - follow directly
                follow, created = Follow.objects.get_or_create(
                    follower=request.user,
                    following=user_to_follow
                )
                if created:
                    user_to_follow.followers_count += 1
                    request.user.following_count += 1
                    user_to_follow.save()
                    request.user.save()
                    message = "You are now following this user!"
                    followed = True
                else:
                    message = "You are already following this user."
                    followed = False
    else:
        message = "You cannot follow yourself."
        followed = False
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'followed': followed,
            'message': message,
            'is_private': user_to_follow.is_private
        })
    
    messages.success(request, message)
    return redirect('accounts:profile', username=username)


@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(
        follower=request.user,
        following=user_to_unfollow
    ).first()
    if follow:
        follow.delete()
        user_to_unfollow.followers_count -= 1
        request.user.following_count -= 1
        user_to_unfollow.save()
        request.user.save()
    return redirect('accounts:profile', username=username)


def followers_list(request, username):
    user = get_object_or_404(User, username=username)
    followers = Follow.objects.filter(following=user).select_related('follower')
    
    # Get the IDs of users that the current user is following
    following_ids = request.user.following.values_list('following_id', flat=True)
    
    return render(request, 'accounts/followers_list.html', {
        'user': user,
        'followers': followers,
        'following_ids': following_ids
    })


def following_list(request, username):
    user = get_object_or_404(User, username=username)
    following = Follow.objects.filter(follower=user).select_related('following')
    
    # Get the IDs of users that the current user is following
    following_ids = request.user.following.values_list('following_id', flat=True)
    
    return render(request, 'accounts/following_list.html', {
        'user': user,
        'following': following,
        'following_ids': following_ids
    })


@login_required
def follow_requests_list(request):
    """View to list all follow requests for the current user"""
    follow_requests = FollowRequest.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user').order_by('-created_at')
    
    # Mark notifications as read
    FollowRequestNotification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)
    
    return render(request, 'accounts/follow_requests.html', {
        'follow_requests': follow_requests
    })


@login_required
def accept_follow_request(request, request_id):
    """Accept a follow request"""
    follow_request = get_object_or_404(
        FollowRequest,
        id=request_id,
        to_user=request.user,
        status='pending'
    )
    
    # Create the follow relationship
    follow, created = Follow.objects.get_or_create(
        follower=follow_request.from_user,
        following=request.user
    )
    
    if created:
        follow_request.from_user.following_count += 1
        request.user.followers_count += 1
        follow_request.from_user.save()
        request.user.save()
    
    # Update follow request status
    follow_request.status = 'accepted'
    follow_request.save()
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'action': 'accepted'})
    
    messages.success(request, f"You accepted {follow_request.from_user.username}'s follow request!")
    return redirect('accounts:follow_requests')


@login_required
def reject_follow_request(request, request_id):
    """Reject a follow request"""
    follow_request = get_object_or_404(
        FollowRequest,
        id=request_id,
        to_user=request.user,
        status='pending'
    )
    
    # Update follow request status
    follow_request.status = 'rejected'
    follow_request.save()
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'action': 'rejected'})
    
    messages.info(request, f"You rejected {follow_request.from_user.username}'s follow request.")
    return redirect('accounts:follow_requests')


@login_required
def follow_requests_count(request):
    """API endpoint to get unread follow requests count"""
    count = FollowRequestNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'count': count})
