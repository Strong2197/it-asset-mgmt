from django.urls import path
from . import views

urlpatterns = [
    path('', views.asset_list, name='asset_list'),
    path('new/', views.asset_create, name='asset_create'),
    path('edit/<int:pk>/', views.asset_update, name='asset_update'),
    path('export/', views.export_assets_xlsx, name='export_assets_xlsx'),
    path('<int:pk>/clone/', views.asset_clone, name='asset_clone'),
]