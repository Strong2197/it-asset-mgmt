from django.urls import path
from . import views

urlpatterns = [
    path('', views.AssetListView.as_view(), name='asset_list'),
    path('new/', views.AssetCreateView.as_view(), name='asset_create'),
    path('edit/<int:pk>/', views.AssetUpdateView.as_view(), name='asset_update'),
    path('export/', views.export_assets_xlsx, name='export_assets_xlsx'), # Залишається як функція
    path('<int:pk>/clone/', views.AssetCloneView.as_view(), name='asset_clone'),
    path('<int:pk>/archive/', views.AssetArchiveView.as_view(), name='asset_archive'),
]