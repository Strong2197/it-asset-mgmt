from django.urls import path
from . import views

urlpatterns = [
    path('', views.service_list, name='service_list'),
    path('create/', views.service_create, name='service_create'),
    path('<int:pk>/update/', views.service_update, name='service_update'),

    # API для автозаповнення відділу
    path('api/get-department/', views.get_last_department, name='get_last_department'),

    path('<int:pk>/receive/', views.service_receive_from_repair, name='service_receive'),
    path('<int:pk>/return/', views.service_quick_return, name='service_return'),
    path('print-preview/', views.print_preview, name='print_preview'),
    path('save_report/', views.save_report, name='save_report'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/edit/', views.report_edit, name='report_edit'),
    path('item/<int:pk>/receive/', views.item_receive, name='item_receive'),
    path('item/<int:pk>/return/', views.item_return, name='item_return'),
]