from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.FeedView.as_view(), name='feed'),
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('create/', views.create_post, name='create_post'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='delete_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('post/<int:post_id>/comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('user/<str:username>/posts/', views.UserPostsView.as_view(), name='user_posts'),
    path('explore/', views.ExploreView.as_view(), name='explore'),
    path('search/', views.search, name='search'),
    path('notifications/', views.NotificationView.as_view(), name='notifications'),
    path('notifications/mark-read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/unread-count/', views.unread_notification_count, name='unread_notification_count'),
    path('api/popular-accounts/', views.popular_accounts, name='popular_accounts'),
    path('api/suggested-accounts/', views.suggested_accounts, name='suggested_accounts'),
    path('create-story/', views.create_story, name='create_story'),
    path('story/<int:story_id>/', views.story_detail, name='story_detail'),
]
