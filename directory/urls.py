from django.urls import path
from . import views

urlpatterns = [
    path('', views.DirectoryListView.as_view(), name='directory_list'),
    path('new/', views.DirectoryCreateView.as_view(), name='directory_create'),
    path('<int:pk>/edit/', views.DirectoryUpdateView.as_view(), name='directory_update'),
    path('<int:pk>/delete/', views.DirectoryDeleteView.as_view(), name='directory_delete'),
]