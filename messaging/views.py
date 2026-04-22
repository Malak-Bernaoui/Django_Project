from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from .models import Conversation, Message, MessageRequest, MessageRequestStatus

class InboxView(LoginRequiredMixin, ListView):
    """View for user's message inbox"""
    model = Conversation
    template_name = 'messaging/inbox.html'
    context_object_name = 'conversations'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user),
            is_active=True
        ).select_related('participant1', 'participant2').prefetch_related('messages')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message_requests'] = MessageRequest.objects.filter(
            recipient=self.request.user,
            status='pending'
        ).select_related('sender')
        return context

class ConversationView(LoginRequiredMixin, DetailView):
    """View for individual conversation"""
    model = Conversation
    template_name = 'messaging/conversation.html'
    context_object_name = 'conversation'
    
    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(
            Q(participant1=user) | Q(participant2=user),
            is_active=True
        ).select_related('participant1', 'participant2').prefetch_related('messages__sender')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.object
        
        # Mark unread messages as read
        unread_messages = conversation.messages.filter(
            ~Q(sender=self.request.user),
            is_read=False
        )
        for message in unread_messages:
            message.mark_as_read()
        
        context['messages'] = conversation.messages.all().order_by('created_at')
        return context

class MessageRequestsView(LoginRequiredMixin, ListView):
    """View for message requests"""
    model = MessageRequest
    template_name = 'messaging/message_requests.html'
    context_object_name = 'message_requests'
    paginate_by = 20
    
    def get_queryset(self):
        return MessageRequest.objects.filter(
            recipient=self.request.user,
            status='pending'
        ).select_related('sender')

@login_required
def start_conversation(request, username):
    """Start a new conversation or create message request"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    recipient = get_object_or_404(User, username=username)
    
    if recipient == request.user:
        return JsonResponse({'error': 'Cannot message yourself'}, status=400)
    
    # Check if users can message each other directly
    if MessageRequestStatus.can_message(request.user, recipient):
        # Create or get existing conversation
        conversation, created = Conversation.objects.get_or_create(
            participant1=min(request.user, recipient, key=lambda u: u.id),
            participant2=max(request.user, recipient, key=lambda u: u.id),
            defaults={'is_active': True}
        )
        return JsonResponse({
            'success': True,
            'conversation_id': conversation.id,
            'can_message': True
        })
    else:
        # Need to send message request
        return JsonResponse({
            'success': True,
            'can_message': False,
            'message': 'You need to send a message request first'
        })

@login_required
@require_POST
def send_message_request(request, username):
    """Send a message request"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    recipient = get_object_or_404(User, username=username)
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'error': 'Message content is required'}, status=400)
    
    # Check if request already exists
    existing_request = MessageRequest.objects.filter(
        sender=request.user,
        recipient=recipient,
        status='pending'
    ).first()
    
    if existing_request:
        return JsonResponse({'error': 'Message request already sent'}, status=400)
    
    # Create message request
    message_request = MessageRequest.objects.create(
        sender=request.user,
        recipient=recipient,
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'message_request_id': message_request.id
    })

@login_required
@require_POST
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Verify user is part of conversation
    if request.user not in [conversation.participant1, conversation.participant2]:
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'error': 'Message content is required'}, status=400)
    
    # Create message
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content
    )
    
    # Update conversation timestamp
    conversation.updated_at = timezone.now()
    conversation.save()
    
    return JsonResponse({
        'success': True,
        'message_id': message.id,
        'content': message.content,
        'created_at': message.created_at.isoformat(),
        'sender': request.user.username
    })

@login_required
@require_POST
def accept_message_request(request, request_id):
    """Accept a message request"""
    message_request = get_object_or_404(MessageRequest, id=request_id, recipient=request.user)
    
    if message_request.status != 'pending':
        return JsonResponse({'error': 'Request already processed'}, status=400)
    
    # Accept the request
    conversation = message_request.accept()
    
    # Grant messaging permission
    MessageRequestStatus.grant_permission(message_request.sender, message_request.recipient)
    
    return JsonResponse({
        'success': True,
        'conversation_id': conversation.id if conversation else None
    })

@login_required
@require_POST
def decline_message_request(request, request_id):
    """Decline a message request"""
    message_request = get_object_or_404(MessageRequest, id=request_id, recipient=request.user)
    
    if message_request.status != 'pending':
        return JsonResponse({'error': 'Request already processed'}, status=400)
    
    message_request.decline()
    
    return JsonResponse({'success': True})

@login_required
def search_users(request):
    """Search for users to message"""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'users': []})
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(id=request.user.id)[:10]
    
    users_data = []
    for user in users:
        can_message = MessageRequestStatus.can_message(request.user, user)
        users_data.append({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'can_message': can_message
        })
    
    return JsonResponse({'users': users_data})
