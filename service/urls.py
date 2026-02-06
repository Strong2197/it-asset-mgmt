from django.urls import path
from . import views

urlpatterns = [
    path('', views.service_list, name='service_list'),
    path('new/', views.service_create, name='service_create'),
    path('edit/<int:pk>/', views.service_update, name='service_update'),

    # Нові функції
    path('return/<int:pk>/', views.service_quick_return, name='service_quick_return'),  # Швидке повернення

    path('print-preview/', views.print_preview, name='print_preview'),  # Попередній перегляд
    path('save-report/', views.save_report, name='save_report'),  # Кнопка "Зберегти"

    path('reports/', views.report_list, name='report_list'),  # Історія
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),  # Друк старого звіту
]