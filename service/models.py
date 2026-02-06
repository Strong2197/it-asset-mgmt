from django.db import models
from django.utils import timezone


class ServiceTask(models.Model):
    TASK_TYPES = [
        ('refill', 'Заправка картриджа'),
        ('repair', 'Ремонт техніки'),
    ]

    # Поле asset видалено. Тепер пишемо назву тільки вручну.
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='refill', verbose_name="Тип роботи")
    device_name = models.CharField(max_length=200, verbose_name="Назва картриджа/принтера")

    requester_name = models.CharField(max_length=100, verbose_name="ПІБ (хто дав)")
    department = models.CharField(max_length=100, verbose_name="Відділ/Кабінет")

    date_received = models.DateField(default=timezone.now, verbose_name="Дата отримання")
    date_sent = models.DateField(blank=True, null=True, verbose_name="Дата відправки сервісу")
    date_returned = models.DateField(blank=True, null=True, verbose_name="Дата повернення")

    description = models.TextField(blank=True, verbose_name="Опис проблеми/робіт")
    is_completed = models.BooleanField(default=False, verbose_name="Завершено")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Заявка в сервіс"
        verbose_name_plural = "Журнал ремонтів та заправок"
        ordering = ['-date_received']

    def __str__(self):
        return f"{self.device_name} ({self.requester_name})"