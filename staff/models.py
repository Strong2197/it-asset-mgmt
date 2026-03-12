from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.validators import RegexValidator
import os

class Employee(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ПІБ")
    position = models.CharField(max_length=100, verbose_name="Посада")
    department = models.CharField(max_length=100, verbose_name="Відділ")
    
    # Валідатор для формату 000-000-00-00
    phone_regex = RegexValidator(
        regex=r'^\d{3}-\d{3}-\d{2}-\d{2}$', 
        message="Телефон має бути у форматі: 000-000-00-00"
    )
    phone = models.CharField(validators=[phone_regex], max_length=20, blank=True, verbose_name="Телефон")
    
    rnokpp = models.CharField(max_length=15, blank=True, verbose_name="РНОКПП (ІПН)")
    is_dismissed = models.BooleanField(default=False, verbose_name="Звільнений")

    appointment_date = models.DateField(null=True, blank=True, verbose_name="Дата призначення")
    appointment_order_number = models.CharField(max_length=50, blank=True, verbose_name="№ Наказу про призначення")
    appointment_order_file = models.FileField(upload_to='orders/appointment/', null=True, blank=True, verbose_name="Скан наказу (PDF)")
    appointment_order_original_name = models.CharField(max_length=255, blank=True, verbose_name="Ориг. назва наказу")

    dismissal_date = models.DateField(null=True, blank=True, verbose_name="Дата звільнення")
    dismissal_order_number = models.CharField(max_length=50, blank=True, verbose_name="№ Наказу про звільнення")
    dismissal_order_file = models.FileField(upload_to='orders/dismissal/', null=True, blank=True, verbose_name="Скан наказу про звільнення")
    dismissal_order_original_name = models.CharField(max_length=255, blank=True, verbose_name="Ориг. назва наказу про звільнення")

    created_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Зберігаємо початкові стани для відстеження змін історії та файлів
        self.__original_position = self.position
        self.__original_department = self.department
        self.__original_appointment_file = self.appointment_order_file.name if self.appointment_order_file else None
        self.__original_dismissal_file = self.dismissal_order_file.name if self.dismissal_order_file else None

    def save(self, *args, **kwargs):
        # 1. Обробка оригінальних імен нових файлів
        if self.appointment_order_file and not self.appointment_order_original_name:
            self.appointment_order_original_name = os.path.basename(self.appointment_order_file.name)
        if self.dismissal_order_file and not self.dismissal_order_original_name:
            self.dismissal_order_original_name = os.path.basename(self.dismissal_order_file.name)

        # 2. Видалення старого файлу призначення, якщо він був змінений
        if self.__original_appointment_file and self.appointment_order_file.name != self.__original_appointment_file:
            old_path = os.path.join(self.appointment_order_file.storage.location, self.__original_appointment_file)
            if os.path.isfile(old_path):
                os.remove(old_path)
                self.appointment_order_original_name = os.path.basename(self.appointment_order_file.name)

        # 3. Видалення старого файлу звільнення, якщо він був змінений
        if self.__original_dismissal_file and self.dismissal_order_file.name != self.__original_dismissal_file:
            old_path = os.path.join(self.dismissal_order_file.storage.location, self.__original_dismissal_file)
            if os.path.isfile(old_path):
                os.remove(old_path)
                self.dismissal_order_original_name = os.path.basename(self.dismissal_order_file.name)

        is_new = self.pk is None
        super().save(*args, **kwargs)

        # 4. Запис історії кар'єри
        if not is_new and (self.position != self.__original_position or self.department != self.__original_department):
            CareerHistory.objects.create(
                employee=self,
                previous_position=self.__original_position,
                new_position=self.position,
                previous_department=self.__original_department,
                new_department=self.department
            )

    def __str__(self): return self.full_name

    class Meta:
        verbose_name = "Працівник"
        verbose_name_plural = "Штатний розпис"
        ordering = ['full_name']

class KepCertificate(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='certificates')
    file = models.FileField(upload_to='kep_certs/', verbose_name="Файл сертифікату")
    original_name = models.CharField(max_length=255, blank=True, verbose_name="Оригінальна назва")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_file = self.file.name if self.file else None

    def save(self, *args, **kwargs):
        # Оновлення імені при завантаженні
        if self.file and not self.original_name:
            self.original_name = os.path.basename(self.file.name)
        
        # Видалення фізичного файлу при заміні
        if self.__original_file and self.file.name != self.__original_file:
            old_path = os.path.join(self.file.storage.location, self.__original_file)
            if os.path.isfile(old_path):
                os.remove(old_path)
                self.original_name = os.path.basename(self.file.name)
                
        super().save(*args, **kwargs)

    def filename(self):
        return self.original_name if self.original_name else os.path.basename(self.file.name)

class CareerHistory(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='career_history', verbose_name="Працівник")
    date_changed = models.DateField(auto_now_add=True, verbose_name="Дата зміни")
    previous_position = models.CharField(max_length=100, blank=True, verbose_name="Минула посада")
    new_position = models.CharField(max_length=100, blank=True, verbose_name="Нова посада")
    previous_department = models.CharField(max_length=100, blank=True, verbose_name="Минулий відділ")
    new_department = models.CharField(max_length=100, blank=True, verbose_name="Новий відділ")
    notes = models.CharField(max_length=200, blank=True, verbose_name="Примітка")

    class Meta:
        verbose_name = "Запис історії"
        verbose_name_plural = "Історія переміщень"
        ordering = ['-date_changed']

# Сигнали для ПОВНОГО видалення об'єктів
@receiver(post_delete, sender=KepCertificate)
def delete_kep_file(sender, instance, **kwargs):
    if instance.file and os.path.isfile(instance.file.path):
        os.remove(instance.file.path)

@receiver(post_delete, sender=Employee)
def delete_employee_files(sender, instance, **kwargs):
    for field in [instance.appointment_order_file, instance.dismissal_order_file]:
        if field and os.path.isfile(field.path):
            os.remove(field.path)