from django.db import models
from users.models import CustomUser

class VisionPrediction(models.Model):
    url = models.TextField(primary_key=True)
    title = models.TextField()
    description = models.TextField()
    image = models.TextField()
    confidence_score = models.FloatField()

    class Meta:
        managed = False
        db_table = 'predictions_yolo'
        app_label = 'core'

class ErrorImage(models.Model):
    url = models.URLField()
    image = models.TextField()

    class Meta:
        managed = False
        db_table = 'errors_images'
        app_label = 'core'


class AnnotationManuelle(models.Model):
    url = models.URLField()
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_confirmed_weapon = models.BooleanField()
    date_annotation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'annotation_manuelle'
        unique_together = ('url', 'user')  # un seul vote par utilisateur