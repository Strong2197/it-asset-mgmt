from django.urls import path
from . import views

urlpatterns = [
    path('api/get/', views.get_tasks, name='todo_get'),
    path('api/add/', views.add_task, name='todo_add'),
    path('api/toggle/<int:pk>/', views.toggle_task, name='todo_toggle'),
    path('api/delete/<int:pk>/', views.delete_task, name='todo_delete'),
]