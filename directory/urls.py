from django.urls import path
from . import views

urlpatterns = [
    path('', views.directory_list, name='directory_list'),
    path('new/', views.directory_create, name='directory_create'),
    path('<int:pk>/edit/', views.directory_update, name='directory_update'),
    path('<int:pk>/delete/', views.directory_delete, name='directory_delete'),
]