from django.db import models
from django.utils import timezone


class ServiceTask(models.Model):
    TASK_TYPES = [
        ('repair', 'Ремонт'),
        ('refill', 'Заправка'),
        ('maintenance', 'Обслуговування'),
        ('drum_clean', 'Чистка драм-юніта'),
    ]

    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='refill', verbose_name="Тип робіт")
    device_name = models.CharField(max_length=200, verbose_name="Назва пристрою/Картриджу")
    requester_name = models.CharField(max_length=100, verbose_name="Замовник (ПІБ)")
    department = models.CharField(max_length=100, verbose_name="Відділ")

    date_received = models.DateField(default=timezone.now, verbose_name="Дата отримання")
    date_sent = models.DateField(null=True, blank=True, verbose_name="Дата відправки")

    # Поле, яке визначає, чи повернувся картридж на склад
    date_back_from_service = models.DateField(null=True, blank=True, verbose_name="Повернуто з сервісу")

    date_returned = models.DateField(null=True, blank=True, verbose_name="Дата повернення клієнту")

    description = models.TextField(blank=True, verbose_name="Опис проблеми")
    is_completed = models.BooleanField(default=False, verbose_name="Виконано")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_name} ({self.department})"


class ServiceReport(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення")
    tasks = models.ManyToManyField(ServiceTask, verbose_name="Картриджі в акті")

    def __str__(self):
        return f"Акт №{self.id} від {self.created_at.strftime('%d.%m.%Y')}"

    # --- ВЛАСТИВІСТЬ ДЛЯ ПЕРЕВІРКИ СТАТУСУ ---
    @property
    def is_archived(self):
        """
        Повертає True, якщо хоча б одна позиція з цього акту
        вже повернулася з сервісу (має дату повернення).
        """
        return self.tasks.filter(date_back_from_service__isnull=False).exists()