from django.db import models


class Document(models.Model):
    TYPE_CHOICES = [
        ('driver', 'Драйвер / Програма'),
        ('instruction', 'Інструкція'),
        ('template', 'Шаблон документу'),
        ('other', 'Інше'),
    ]

    title = models.CharField(max_length=200, verbose_name="Назва")
    doc_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other', verbose_name="Тип")

    # Змінили FileField на URLField
    google_drive_link = models.URLField(verbose_name="Посилання на Google Drive/Cloud")

    description = models.TextField(blank=True, verbose_name="Опис")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Файл (посилання)"
        verbose_name_plural = "База знань"

    def __str__(self):
        return self.title