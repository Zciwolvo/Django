from django.db import models


class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)  # Set default value

    def toggle_completed(self):
        self.completed = not self.completed
        self.save()

    def __str__(self):
        return self.title