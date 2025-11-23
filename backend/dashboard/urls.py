from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('users/', views.UserManagementView.as_view(), name='user_management'),
]