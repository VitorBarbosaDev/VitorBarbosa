from django.db import models
from cloudinary.models import CloudinaryField

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = CloudinaryField('image', blank=True, null=True)
    github_link = models.URLField()
    live_link = models.URLField(blank=True, null=True)
    technologies = models.CharField(max_length=200)

    def __str__(self):
        return self.title

class CV(models.Model):
    resume = CloudinaryField('resume')

    def __str__(self):
        return "CV"
