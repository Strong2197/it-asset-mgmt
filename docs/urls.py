from django.urls import path
from . import views

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='doc_list'),
    path('new/', views.DocumentCreateView.as_view(), name='doc_create'),
    path('edit/<int:pk>/', views.DocumentUpdateView.as_view(), name='doc_update'),
    path('<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='doc_delete'),
]