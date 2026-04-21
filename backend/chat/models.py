from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class ChatSession(models.Model):
    """Stores individual chat sessions"""
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
    """Stores individual messages in a chat session"""
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    sources = models.JSONField(null=True, blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}"
