from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class UserProfile(models.Model):
    ROLES = [('admin', 'Admin'), ('user', 'User')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLES, default='user')

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class KnowledgeDocument(models.Model):
    STATUS = [('indexed', 'Indexed'), ('failed', 'Failed')]
    name = models.CharField(max_length=255, unique=True)
    file_type = models.CharField(max_length=10)
    size_bytes = models.PositiveBigIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS, default='indexed')
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.name


class ChatSession(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='sessions'
    )
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Session {self.session_id}"


class Message(models.Model):
    MESSAGE_TYPES = [('user', 'User'), ('assistant', 'Assistant')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    sources = models.JSONField(null=True, blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}"
