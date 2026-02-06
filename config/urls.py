from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render


# Функція для головної сторінки
def home_view(request):
    return render(request, 'index.html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),

    # Підключаємо наші додатки
    path('inventory/', include('inventory.urls')),
    path('service/', include('service.urls')),
    path('docs/', include('docs.urls')),

]

# Налаштування медіа-файлів (для картинок/документів)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)