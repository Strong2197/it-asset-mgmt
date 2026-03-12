from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

# Імпортуємо home_view з додатку inventory
from inventory.views import home_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'), # Викликаємо імпортовану функцію

    path('inventory/', include('inventory.urls')),
    path('service/', include('service.urls')),
    path('docs/', include('docs.urls')),
    path('staff/', include('staff.urls')),
    path('directory/', include('directory.urls')),
    path('todo/', include('todo.urls')),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
    re_path(r'^static/(?P<path>.*)$', serve, {
        'document_root': settings.STATIC_ROOT,
    }),
]