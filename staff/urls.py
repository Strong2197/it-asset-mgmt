from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.staff_create, name='staff_create'), # ПЕРШИМ
    path('', views.staff_list, name='staff_list'),           # ОСТАННІМ
    path('<int:pk>/update/', views.staff_update, name='staff_update'),
    path('<int:pk>/delete/', views.staff_delete, name='staff_delete'),
    path('cert/<int:pk>/delete/', views.cert_delete, name='cert_delete'),
]