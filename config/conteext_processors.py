import os
from django.conf import settings
from django.core.cache import cache

def disk_usage_monitor(request):
    """
    Рахує зайняте місце в домашній директорії (включно з venv, медіа, БД).
    Результат кешується на 5 хвилин.
    """
    CACHE_KEY = 'pythonanywhere_disk_usage'
    CACHE_TIMEOUT = 300  # 300 секунд = 5 хвилин

    # Спробуємо отримати дані з кешу
    stats = cache.get(CACHE_KEY)

    if not stats:
        # Ліміт 512 МБ (у байтах)
        LIMIT_MB = 512
        LIMIT_BYTES = LIMIT_MB * 1024 * 1024
        
        # Починаємо сканувати з батьківської папки проекту (тобто з /home/username/)
        # Це захопить і проект, і venv, якщо він поруч
        root_path = settings.BASE_DIR.parent 
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                # Оптимізація: не заходимо в кеш пітона, це пришвидшить підрахунок
                if '__pycache__' in dirnames:
                    dirnames.remove('__pycache__')
                
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    # Додаємо розмір файлу, якщо це не символічне посилання
                    if os.path.exists(fp) and not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
        except Exception:
            pass # Ігноруємо помилки доступу, якщо такі будуть

        # Розрахунки
        used_mb = round(total_size / (1024 * 1024), 1)
        free_mb = round((LIMIT_BYTES - total_size) / (1024 * 1024), 1)
        percent = round((total_size / LIMIT_BYTES) * 100, 1)
        
        # Вибір кольору для прогрес-бару
        color = 'success' # Зелений
        if percent > 70: color = 'warning' # Жовтий
        if percent > 90: color = 'danger' # Червоний (Критично)

        stats = {
            'used': used_mb,
            'free': free_mb,
            'total': LIMIT_MB,
            'percent': percent,
            'color': color,
            'is_critical': percent > 95
        }
        
        # Записуємо в кеш
        cache.set(CACHE_KEY, stats, CACHE_TIMEOUT)

    return {'disk_usage': stats}
