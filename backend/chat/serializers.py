from rest_framework import serializers
from .models import ChatSession, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'message_type', 'content', 'sources', 'feedback', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['session_id', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['session_id', 'created_at', 'updated_at']


class ChatRequestSerializer(serializers.Serializer):
    """Serializer for incoming chat requests"""
    session_id = serializers.UUIDField(required=False, allow_null=True)
    user_message = serializers.CharField(max_length=1000, min_length=1, trim_whitespace=True)


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for outgoing chat responses"""
    answer = serializers.CharField()
    sources = serializers.ListField(child=serializers.CharField())
    session_id = serializers.UUIDField()
    message_id = serializers.IntegerField()
