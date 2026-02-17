import os
import subprocess
from django.core.cache import cache

def disk_usage_monitor(request):
    """
    Рахує реальне використання диска за допомогою системної команди `du`.
    Це враховує розмір блоків на диску (block size overhead), 
    тому цифра буде відповідати тій, що на дашборді.
    """
    CACHE_KEY = 'pythonanywhere_disk_usage'
    CACHE_TIMEOUT = 6000  # Кешуємо на 5 хвилин

    stats = cache.get(CACHE_KEY)

    if not stats:
        # Ліміт 512 МБ
        LIMIT_MB = 512
        LIMIT_BYTES = LIMIT_MB * 1024 * 1024
        
        root_path = os.path.expanduser('~') # /home/ifit/
        
        total_size = 0
        try:
            # Виконуємо команду 'du -s' (disk usage summary)
            # Вона повертає кількість зайнятих блоків (у кілобайтах)
            cmd = ['du', '-s', root_path]
            
            # Запускаємо процес і отримуємо результат
            output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL).decode('utf-8')
            
            # Результат виглядає як: "119804 /home/ifit"
            kb_used = int(output.split()[0])
            
            # Переводимо кілобайти в байти
            total_size = kb_used * 1024
            
        except Exception:
            # Якщо команда не спрацювала, повертаємо 0 або пробуємо старий метод
            total_size = 0

        # Розрахунки
        used_mb = round(total_size / (1024 * 1024), 1)
        
        # Іноді може бути більше 100%, якщо ліміт перевищено
        if used_mb > LIMIT_MB:
            free_mb = 0
            percent = 100
        else:
            free_mb = round((LIMIT_BYTES - total_size) / (1024 * 1024), 1)
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
