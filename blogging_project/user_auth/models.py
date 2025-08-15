from django.contrib.auth.models import AbstractUser
from django.db import models

class BaseModel(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "user_auth.User", 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name="%(class)s_created"
    )

    class Meta:
        abstract = True

class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.username
