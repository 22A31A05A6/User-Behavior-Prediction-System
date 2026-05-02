from django.db import models

# Create your models here.
from django.db import models
from django.utils import timezone

class UserRegister(models.Model):
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField()
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    mobile = models.CharField(max_length=15)
    profile_pic = models.ImageField(upload_to='profiles/')
    status = models.CharField(max_length=20, default='Unauthorized')

    def __str__(self):
        return self.username
from django.contrib.auth.models import User
from django.utils import timezone

class Post(models.Model):

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
    ]

    name = models.CharField(max_length=100, default="Unknown")
    content = models.TextField()
    image = models.ImageField(upload_to='posts/')
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')

    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # 👈 important
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


from django.contrib.auth.models import User

class Video(models.Model):

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private')
    ]

    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='videos/')

    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')

    upload_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.filename
from django.utils import timezone
from django.contrib.auth.models import User
class IntentionSequence(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    intention = models.CharField(max_length=200)
    prediction = models.CharField(max_length=200)
    sequence = models.TextField()
    time = models.DateTimeField(auto_now_add=True)
    confidence = models.FloatField(default=0)
    behavior_status = models.CharField(
        max_length=20,
        default="Positive"   # Positive / Negative
    )

    def __str__(self):
        return self.user_id
    
class Behavior(models.Model):
    behavior = models.CharField(max_length=50)
    event_id = models.IntegerField()
    desire_id = models.IntegerField()


class UserIntention(models.Model):
    username = models.CharField(max_length=100)
    stage = models.TextField()


class Intention(models.Model):
    username = models.CharField(max_length=100)
    uintention = models.CharField(max_length=100)
class FriendRequest(models.Model):
    sname = models.CharField(max_length=100)   # receiver
    uname = models.CharField(max_length=100)   # sender
    email = models.EmailField()
    gender = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

class Message(models.Model):
    sender = models.CharField(max_length=100)
    receiver = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Group(models.Model):
    groupname = models.CharField(max_length=150)
    admin = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.groupname

class Comment(models.Model):
    imagename = models.CharField(max_length=255)
    comment = models.TextField()
    content = models.TextField()
    uname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.uname} - {self.imagename}"
    
class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    username = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.group.groupname} - {self.username}"

# users/models.py

class GroupRequest(models.Model):
    groupname = models.CharField(max_length=150)
    gadmin = models.CharField(max_length=100)
    name = models.CharField(max_length=100)   # invited user
    status = models.CharField(max_length=20, default="pending")

    def __str__(self):
        return f"{self.groupname} -> {self.name}"


class Friend(models.Model):
    user1 = models.CharField(max_length=100)
    user2 = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user1} - {self.user2}"

from django.db import models
from django.contrib.auth.models import User


class UserBehavior(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    action = models.CharField(max_length=100)     # login, upload_post, send_msg
    page = models.CharField(max_length=100)       # page name
    description = models.TextField(null=True, blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    session_id = models.CharField(max_length=200, null=True, blank=True)
    ip_address = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"







