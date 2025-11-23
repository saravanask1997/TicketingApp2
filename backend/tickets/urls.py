from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListView.as_view(), name='list'),
    path('create/', views.TicketCreateView.as_view(), name='create'),
    path('<uuid:pk>/', views.TicketDetailView.as_view(), name='detail'),
    path('<uuid:pk>/edit/', views.TicketUpdateView.as_view(), name='edit'),
    path('<uuid:ticket_id>/assign/', views.assign_ticket, name='assign'),
    path('<uuid:ticket_id>/status/', views.update_status, name='update_status'),
    path('<uuid:ticket_id>/comment/', views.add_comment, name='add_comment'),
    path('my/', views.MyTicketsView.as_view(), name='my_tickets'),
]