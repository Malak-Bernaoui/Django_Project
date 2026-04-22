from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Conversation(models.Model):
    """Conversation between two users"""
    participant1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations1')
    participant2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations2')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['participant1', 'participant2']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Conversation between {self.participant1.username} and {self.participant2.username}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if user == self.participant1:
            return self.participant2
        return self.participant1
    
    def get_last_message(self):
        """Get the last message in the conversation"""
        return self.messages.order_by('-created_at').first()

class Message(models.Model):
    """Individual message in a conversation"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} in {self.conversation}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

class MessageRequest(models.Model):
    """Message request for users who don't follow each other"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_message_requests')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_message_requests')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
        ],
        default='pending'
    )
    
    class Meta:
        unique_together = ['sender', 'recipient']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Message request from {self.sender.username} to {self.recipient.username}"
    
    def accept(self):
        """Accept the message request and create conversation"""
        if self.status == 'pending':
            self.status = 'accepted'
            self.save()
            
            # Create conversation
            conversation, created = Conversation.objects.get_or_create(
                participant1=min(self.sender, self.recipient, key=lambda u: u.id),
                participant2=max(self.sender, self.recipient, key=lambda u: u.id)
            )
            
            # Add the initial message
            Message.objects.create(
                conversation=conversation,
                sender=self.sender,
                content=self.content
            )
            
            return conversation
        return None
    
    def decline(self):
        """Decline the message request"""
        if self.status == 'pending':
            self.status = 'declined'
            self.save()

class MessageRequestStatus(models.Model):
    """Track which users can message each other without requests"""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_permissions1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_permissions2')
    can_message = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user1', 'user2']
    
    def __str__(self):
        status = "can message" if self.can_message else "cannot message"
        return f"{self.user1.username} {status} {self.user2.username}"
    
    @classmethod
    def can_message(cls, user1, user2):
        """Check if user1 can message user2 directly"""
        # Users can message each other if they follow each other
        if (user1.following.filter(following=user2).exists() and 
            user2.following.filter(following=user1).exists()):
            return True
        
        # Check if permission has been granted
        try:
            permission = cls.objects.get(
                user1=min(user1, user2, key=lambda u: u.id),
                user2=max(user1, user2, key=lambda u: u.id)
            )
            return permission.can_message
        except cls.DoesNotExist:
            return False
    
    @classmethod
    def grant_permission(cls, user1, user2):
        """Grant messaging permission between two users"""
        permission, created = cls.objects.get_or_create(
            user1=min(user1, user2, key=lambda u: u.id),
            user2=max(user1, user2, key=lambda u: u.id),
            defaults={'can_message': True}
        )
        if not created:
            permission.can_message = True
            permission.save()
