from django.db import models

class Task(models.Model):
    # Поле user видалено, тепер завдання спільні
    text = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['is_done', '-created_at']

    def __str__(self):
        return self.text