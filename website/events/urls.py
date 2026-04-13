from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    path('profile-setup/', views.profile_setup, name='profile_setup'),
    path('avatar/', views.avatar_setup, name='avatar_setup'),

    path('main/', views.main_view, name='main'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),

    path('events/', views.events_list, name='events_list'),
    path('events/<int:id>/', views.event_detail, name='event_detail'),
    path('create/', views.event_create, name='event_create'),
    path('edit/<int:id>/', views.event_edit, name='event_edit'),
    path('delete/<int:id>/', views.event_delete, name='event_delete'),
    path('join/<int:id>/', views.join_event, name='join_event'),
    path('leave/<int:id>/', views.leave_event, name='leave_event'),
]