from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('profile/<str:username>/edit/', views.edit_profile, name='edit_profile'),
    path('follow/<str:username>/', views.follow_user, name='follow'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow'),
    path('profile/<str:username>/followers/', views.followers_list, name='followers'),
    path('profile/<str:username>/following/', views.following_list, name='following'),
    path('follow-requests/', views.follow_requests_list, name='follow_requests'),
    path('follow-requests/<int:request_id>/accept/', views.accept_follow_request, name='accept_follow_request'),
    path('follow-requests/<int:request_id>/reject/', views.reject_follow_request, name='reject_follow_request'),
    path('api/follow-requests-count/', views.follow_requests_count, name='follow_requests_count'),
]
