from django.urls import path
from . import views

app_name = 'messages'

urlpatterns = [
    path('', views.InboxView.as_view(), name='inbox'),
    path('conversation/<int:pk>/', views.ConversationView.as_view(), name='conversation'),
    path('requests/', views.MessageRequestsView.as_view(), name='message_requests'),
    path('start/<str:username>/', views.start_conversation, name='start_conversation'),
    path('send-request/<str:username>/', views.send_message_request, name='send_message_request'),
    path('send/<int:conversation_id>/', views.send_message, name='send_message'),
    path('accept-request/<int:request_id>/', views.accept_message_request, name='accept_request'),
    path('decline-request/<int:request_id>/', views.decline_message_request, name='decline_request'),
    path('search-users/', views.search_users, name='search_users'),
]
