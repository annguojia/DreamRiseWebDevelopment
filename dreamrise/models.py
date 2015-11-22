from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from decimal import *

class Activity(models.Model):
    title = models.CharField(max_length=100, default="")
    image = models.FileField(upload_to='picture') # FIXME
    image_url = models.CharField(blank=True, max_length=2048)
    content_type = models.CharField(max_length=50) # FIXME
    description = models.TextField(max_length=5000)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    fund_start = models.DateField(auto_now=True)
    fund_end = models.DateField()
    fund_goal = models.PositiveIntegerField()
    # fund_goal = models.DecimalField(max_digits=8, decimal_places=2)
    fund_amount = models.PositiveIntegerField(blank=True, default=0)
    # fund_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, default=Decimal('0'))
    starter = models.ForeignKey(User)
    funder = models.ManyToManyField(User, related_name='starter')

    def __unicode__(self):
        return str(self.id)


class Like_Activity(models.Model):
    user = models.ForeignKey(User)
    activity = models.ForeignKey(Activity)
    creation_time = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return str(self.id)


class Funding_Transaction(models.Model):
    STATUS_CHOICES = (
        ('I', 'Complete'),
        ('C', 'Incomplete'),
    )

    uuid = models.CharField(max_length=32, unique=True)
    activity = models.ForeignKey(Activity)
    funder = models.ForeignKey(User)
    time = models.DateTimeField(auto_now=True)
    amount = models.PositiveIntegerField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='I')
    stripe_token = models.CharField(max_length=300, blank=True)

    def __unicode__(self):
        return str(self.amount)


class Planning(models.Model):
    activity = models.OneToOneField(Activity)
    author = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.activity)


class Phase(models.Model):
    due_date = models.DateField(blank=True, null=True)
    title = models.CharField(max_length=80)
    description = models.TextField(blank=True, null=True, max_length=430)
    planning = models.ForeignKey(Planning)
    author = models.ForeignKey(User)

    def __unicode__(self):
        return str(self.description)


class Todo(models.Model):
    phase = models.ForeignKey(Phase)
    author = models.ForeignKey(User)
    content = models.CharField(max_length=80)
    status = models.CharField(blank=True, null=True, max_length=430)

    def __unicode__(self):
        return str(self.content)


class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True)
    avatar = models.ImageField(upload_to='headphotos', blank=True, null=True)
    bio = models.TextField(blank=True, null=True, max_length=430)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], blank=True, max_length=100) # validators should be a list
    content_type = models.CharField(max_length=50)
    avatar_url = models.CharField(blank=True, max_length=2048)

    def __unicode__(self):
        return str(self.user.username)


class Comment(models.Model):
    comment = models.CharField(max_length=160)
    activity = models.ForeignKey(Activity)
    user = models.ForeignKey(User)
    time = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        # return self.comment + ', from: '+str(self.user)+' ,time: '+str(self.time)
        return str(self.comment)


class Update(models.Model):
    title = models.CharField(max_length=80,default="Title")
    content = models.TextField(default="Content")
    activity = models.ForeignKey(Activity)
    author = models.ForeignKey(User)
    date = models.DateField(auto_now=True)

    def __unicode__(self):
        return str(self.title)