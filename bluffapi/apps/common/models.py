from django.db import models


class TimeStampModel(models.Model):
    """
    Model to store the time
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
