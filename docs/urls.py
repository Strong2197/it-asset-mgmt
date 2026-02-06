from django.urls import path
from . import views

urlpatterns = [
    path('', views.doc_list, name='doc_list'),
    path('new/', views.doc_create, name='doc_create'),
    path('edit/<int:pk>/', views.doc_update, name='doc_update'),
]