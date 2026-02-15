# staff/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.staff_list, name='staff_list'),
    path('create/', views.staff_create, name='staff_create'),
    path('<int:pk>/update/', views.staff_update, name='staff_update'),
    path('<int:pk>/dismiss/', views.staff_dismiss, name='staff_dismiss'), # Новий URL
    path('<int:pk>/delete/', views.staff_delete, name='staff_delete'),
    path('cert/<int:pk>/delete/', views.cert_delete, name='cert_delete'),
    path('order/<int:pk>/<str:order_type>/', views.open_order_file, name='open_order_file'),
]