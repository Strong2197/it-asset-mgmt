from django.db import models
from django.utils import timezone

CARTRIDGE_CHOICES = [
    ('Картридж Xerox Phaser 3020, WC3025', 'Картридж Xerox Phaser 3020, WC3025'),
    ('Картридж Canon 725/ HP [CE285A]', 'Картридж Canon 725/ HP [CE285A]'),
    ('Тонер-картридж OKI MB472', 'Тонер-картридж OKI MB472'),
    ('Картридж HP [CF283A]', 'Картридж HP [CF283A]'),
    ('Картридж Canon 103/303/703/HP [Q2612A]', 'Картридж Canon 103/303/703/HP [Q2612A]'),
    ('Картридж HP [CE278A]', 'Картридж HP [CE278A]'),
    ('Картридж Canon FX-10', 'Картридж Canon FX-10'),
    ('Картридж Canon 728', 'Картридж Canon 728'),
    ('Картридж HP [Q7553A]', 'Картридж HP [Q7553A]'),
    ('Картридж Samsung MLT-D101S', 'Картридж Samsung MLT-D101S'),
    ('Картридж Canon 712/ HP [CB435A]', 'Картридж Canon 712/ HP [CB435A]'),
    ('Картридж HP [CE505A]', 'Картридж HP [CE505A]'),
    ('Картридж HP [CB436A]', 'Картридж HP [CB436A]'),
    ('Барабан OKI', 'Барабан OKI'),
    ('Інше', 'Інше (вказати вручну)')
]


class ServiceTask(models.Model):
    TASK_TYPES = [
        ('repair', 'Ремонт'),
        ('refill', 'Заправка'),
        ('maintenance', 'Обслуговування'),
        ('drum_clean', 'Чистка драм-юніта'),
    ]

    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='refill', verbose_name="Тип робіт")

    # Зробили null=True, blank=True, бо тепер ми використовуємо items
    device_name = models.CharField(max_length=200, verbose_name="Назва пристрою/Картриджу", null=True, blank=True)

    requester_name = models.CharField(max_length=100, verbose_name="Замовник (ПІБ)",
                                      blank=True)  # Можна зробити необов'язковим, якщо беремо з відділу
    department = models.CharField(max_length=100, verbose_name="Відділ")

    date_received = models.DateField(default=timezone.now, verbose_name="Дата отримання")
    date_sent = models.DateField(null=True, blank=True, verbose_name="Дата відправки (Акт)")

    # Ці поля залишаємо як "загальні" для закриття заявки, але основна робота буде в items
    date_back_from_service = models.DateField(null=True, blank=True, verbose_name="Повернуто з сервісу (Загальне)")
    date_returned = models.DateField(null=True, blank=True, verbose_name="Дата закриття заявки")

    description = models.TextField(blank=True, verbose_name="Опис проблеми")
    is_completed = models.BooleanField(default=False, verbose_name="Виконано")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.department} ({self.date_received})"


class ServiceTaskItem(models.Model):
    task = models.ForeignKey(ServiceTask, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=100, choices=CARTRIDGE_CHOICES, verbose_name="Тип картриджа/пристрою")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")
    custom_name = models.CharField(max_length=100, blank=True, verbose_name="Уточнення (якщо 'Інше')")

    # --- НОВІ ПОЛЯ ДЛЯ ОКРЕМИХ КАРТРИДЖІВ ---
    date_back_from_service = models.DateField(null=True, blank=True, verbose_name="Повернувся з сервісу")
    date_returned_to_user = models.DateField(null=True, blank=True, verbose_name="Видано клієнту")

    def __str__(self):
        return f"{self.item_name} ({self.quantity} шт.)"


class ServiceReport(models.Model):
    # Змінено: прибрали auto_now_add=True, щоб поле можна було редагувати
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата створення"
    )
    tasks = models.ManyToManyField('ServiceTask', verbose_name="Картриджі в акті")

    def __str__(self):
        return f"Акт №{self.id} від {self.created_at.strftime('%d.%m.%Y')}"

    @property
    def is_archived(self):
        # Логіка архівування залишається без змін [cite: 7]
        has_unissued_items = ServiceTaskItem.objects.filter(
            task__in=self.tasks.all(),
            date_returned_to_user__isnull=True
        ).exists()
        return not has_unissued_items