from django.db import models

class PhonebookEntry(models.Model):
    department = models.CharField(max_length=255, verbose_name="Підрозділ / Відділ")
    code = models.CharField(max_length=20, blank=True, verbose_name="Код відділу")
    email = models.EmailField(blank=True, verbose_name="Загальний Email")

    # --- КЕРІВНИК ---
    chief_name = models.CharField(max_length=150, verbose_name="ПІБ Начальника", blank=True)
    chief_position = models.CharField(max_length=100, default="Начальник відділу", verbose_name="Посада керівника")
    chief_phone = models.CharField(max_length=50, blank=True, verbose_name="Мобільний начальника")
    chief_ip = models.CharField(max_length=20, blank=True, verbose_name="IP телефон начальника")

    # --- ЗАСТУПНИК ---
    deputy_name = models.CharField(max_length=150, verbose_name="ПІБ Заступника", blank=True)
    deputy_phone = models.CharField(max_length=50, blank=True, verbose_name="Мобільний заступника")
    deputy_ip = models.CharField(max_length=20, blank=True, verbose_name="IP телефон заступника")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    def __str__(self):
        return self.department

    class Meta:
        verbose_name = "Запис довідника"
        verbose_name_plural = "Телефонний довідник"
        ordering = ['department']