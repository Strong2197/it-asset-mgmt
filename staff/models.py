from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os

class Employee(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ПІБ")
    position = models.CharField(max_length=100, verbose_name="Посада")
    department = models.CharField(max_length=100, verbose_name="Відділ")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    rnokpp = models.CharField(max_length=15, blank=True, verbose_name="РНОКПП (ІПН)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Працівник"
        verbose_name_plural = "Штатний розпис"
        ordering = ['full_name']

class KepCertificate(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='certificates')
    file = models.FileField(upload_to='kep_certs/', verbose_name="Файл сертифікату")
    original_name = models.CharField(max_length=255, blank=True, verbose_name="Оригінальна назва")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def filename(self):
        return self.original_name if self.original_name else os.path.basename(self.file.name)

# --- НОВИЙ БЛОК ДЛЯ АВТОМАТИЧНОГО ВИДАЛЕННЯ ФАЙЛІВ ---

@receiver(post_delete, sender=KepCertificate)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Видаляє файл із диска після видалення запису з бази даних.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)