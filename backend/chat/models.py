from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class UserProfile(models.Model):
    ROLES = [('admin', 'Admin'), ('user', 'User')]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLES, default='user')

    # Personal context — merged into the system prompt on every chat turn.
    # bio: short free-text description the user writes about themselves.
    # preferences: structured hints (tone, expertise level, etc.).
    bio = models.TextField(blank=True, default='')
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class UserMemory(models.Model):
    """Durable facts the assistant has learned about a specific user.

    Populated by the auto-extraction pass after each assistant reply, and by
    manual entries from the memory management UI. Retrieved alongside the
    shared KB on every chat turn so answers can be personalized."""

    SOURCES = [
        ('auto', 'Auto-extracted'),
        ('manual', 'Manual entry'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memories')
    content = models.TextField()
    source = models.CharField(max_length=10, choices=SOURCES, default='auto')
    # Nullable FK: manual memories have no originating message.
    source_message = models.ForeignKey(
        'Message', on_delete=models.SET_NULL, null=True, blank=True, related_name='extracted_memories',
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_active'])]

    def __str__(self):
        return f"{self.user.username}: {self.content[:60]}"


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
    title = models.CharField(max_length=120, blank=True, default='')
    pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-pinned', '-updated_at']

    def __str__(self):
        return self.title or f"Session {self.session_id}"


class Message(models.Model):
    MESSAGE_TYPES = [('user', 'User'), ('assistant', 'Assistant')]
    FEEDBACK_CHOICES = [(-1, 'Down'), (0, 'None'), (1, 'Up')]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    sources = models.JSONField(null=True, blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    # Observability — populated for assistant messages by the RAG path.
    request_id = models.CharField(max_length=32, blank=True, default='')
    tokens_in = models.PositiveIntegerField(null=True, blank=True)
    tokens_out = models.PositiveIntegerField(null=True, blank=True)
    cost_usd = models.FloatField(null=True, blank=True)

    # User feedback on assistant replies. 0 = no vote.
    feedback = models.SmallIntegerField(choices=FEEDBACK_CHOICES, default=0)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}"
