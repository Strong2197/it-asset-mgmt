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

    is_dismissed = models.BooleanField(default=False, verbose_name="Звільнений")

    # Призначення
    appointment_date = models.DateField(null=True, blank=True, verbose_name="Дата призначення")
    appointment_order_number = models.CharField(max_length=50, blank=True, verbose_name="№ Наказу про призначення")
    appointment_order_file = models.FileField(upload_to='orders/appointment/', null=True, blank=True,
                                              verbose_name="Скан наказу (PDF)")
    # НОВЕ ПОЛЕ
    appointment_order_original_name = models.CharField(max_length=255, blank=True,
                                                       verbose_name="Ориг. назва наказу про призначення")

    # Звільнення
    dismissal_date = models.DateField(null=True, blank=True, verbose_name="Дата звільнення")
    dismissal_order_number = models.CharField(max_length=50, blank=True, verbose_name="№ Наказу про звільнення")
    dismissal_order_file = models.FileField(upload_to='orders/dismissal/', null=True, blank=True,
                                            verbose_name="Скан наказу про звільнення (PDF)")
    # НОВЕ ПОЛЕ
    dismissal_order_original_name = models.CharField(max_length=255, blank=True,
                                                     verbose_name="Ориг. назва наказу про звільнення")

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


# --- АВТОМАТИЧНЕ ВИДАЛЕННЯ ФАЙЛІВ ---
@receiver(post_delete, sender=KepCertificate)
def delete_kep_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)


@receiver(post_delete, sender=Employee)
def delete_employee_files(sender, instance, **kwargs):
    if instance.appointment_order_file and os.path.isfile(instance.appointment_order_file.path):
        os.remove(instance.appointment_order_file.path)
    if instance.dismissal_order_file and os.path.isfile(instance.dismissal_order_file.path):
        os.remove(instance.dismissal_order_file.path)