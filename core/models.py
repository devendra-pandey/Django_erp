from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  null=True, related_name='created_%(class)s')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                  null=True, related_name='updated_%(class)s')
    
    class Meta:
        abstract = True

class Company(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    tax_id = models.CharField(max_length=50)
    logo = models.ImageField(upload_to='company/', null=True, blank=True)
    
    def __str__(self):
        return self.name

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name