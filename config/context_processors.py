import os
from django.core.cache import cache

def disk_usage_monitor(request):
    """
    Рахує реальне зайняте місце в домашній директорії (/home/username).
    Враховує venv, кеш, базу даних, медіа та приховані файли.
    """
    CACHE_KEY = 'pythonanywhere_disk_usage'
    CACHE_TIMEOUT = 300  # Кешуємо на 5 хвилин

    stats = cache.get(CACHE_KEY)

    if not stats:
        # Ваш ліміт (512 МБ)
        LIMIT_MB = 512
        LIMIT_BYTES = LIMIT_MB * 1024 * 1024
        
        # Скануємо всю домашню папку користувача (це точніше, ніж BASE_DIR)
        root_path = os.path.expanduser('~') 
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(root_path):
                # МИ БІЛЬШЕ НЕ ВИКЛЮЧАЄМО __pycache__, бо вони враховуються хостингом
                
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    # Перевіряємо, чи файл існує і не є посиланням
                    if os.path.exists(fp) and not os.path.islink(fp):
                        total_size += os.path.getsize(fp)
        except Exception:
            pass 

        # Конвертуємо в МБ
        used_mb = round(total_size / (1024 * 1024), 1)
        free_mb = round((LIMIT_BYTES - total_size) / (1024 * 1024), 1)
        
        # Захист від ділення на нуль або від'ємних значень
        if used_mb > LIMIT_MB:
            percent = 100
        else:
            percent = round((total_size / LIMIT_BYTES) * 100, 1)
        
        color = 'success'
        if percent > 70: color = 'warning'
        if percent > 90: color = 'danger'

        stats = {
            'used': used_mb,
            'free': free_mb,
            'total': LIMIT_MB,
            'percent': percent,
            'color': color,
            'is_critical': percent > 95
        }
        
        cache.set(CACHE_KEY, stats, CACHE_TIMEOUT)

    return {'disk_usage': stats}
