from django.db import models
import os


class Employee(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ПІБ")
    position = models.CharField(max_length=100, verbose_name="Посада")
    department = models.CharField(max_length=100, verbose_name="Відділ")

    # blank=True означає, що поле може бути пустим
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    rnokpp = models.CharField(max_length=15, blank=True, verbose_name="РНОКПП (ІПН)")

    created_at = models.DateTimeField(auto_now_add=True)

    # ...

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Працівник"
        verbose_name_plural = "Штатний розпис"
        ordering = ['full_name']


# Нова модель для файлів (Сертифікатів)
class KepCertificate(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='certificates')
    file = models.FileField(upload_to='kep_certs/', verbose_name="Файл сертифікату")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def filename(self):
        return os.path.basename(self.file.name)