from django.db import models


class Category(models.Model):
    """Категорія обладнання (Монітор, ПК, ББЖ тощо)"""
    name = models.CharField(max_length=100, verbose_name="Назва категорії")

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self):
        return self.name


class Asset(models.Model):
    """Основна модель майна"""
    ACCOUNT_CHOICES = [
        ('104', 'Рахунок 104 (Основні засоби)'),
        ('113', 'Рахунок 113 (Малоцінні)'),
    ]

    # ЗМІНЕНО: TextField дозволяє зберігати довгі назви/описи
    name = models.TextField(verbose_name="Назва майна")

    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name="Тип")
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name="Інвентарний номер")
    barcode = models.CharField(max_length=50, blank=True, null=True, verbose_name="Баркод")

    responsible_person = models.CharField(max_length=100, verbose_name="Матеріально відповідальний")
    location = models.CharField(max_length=100, blank=True, verbose_name="Кабінет/Локація")
    account = models.CharField(max_length=3, choices=ACCOUNT_CHOICES, verbose_name="Рахунок")

    purchase_date = models.DateField(null=True, blank=True, verbose_name="Дата придбання")
    notes = models.TextField(blank=True, verbose_name="Примітки")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата створення запису")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Останнє редагування")

    is_archived = models.BooleanField(default=False, verbose_name="В архіві")
    archive_reason = models.CharField(max_length=200, blank=True, null=True,
                                      verbose_name="Причина архівування (кому передано/списання)")
    archive_date = models.DateField(blank=True, null=True, verbose_name="Дата архівування")

    class Meta:
        verbose_name = "Майно"
        verbose_name_plural = "Список майна"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.inventory_number})"