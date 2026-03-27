import json
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import uuid

from .models import ChatSession, Message
from .serializers import ChatRequestSerializer, ChatResponseSerializer, ChatSessionSerializer
from .rag import get_rag_system


@api_view(['POST'])
def chat_endpoint(request):
    """
    API endpoint for chat interactions

    Expected JSON payload:
    {
        "session_id": "optional-uuid",
        "user_message": "Your question here"
    }

    Response:
    {
        "answer": "AI response",
        "sources": ["Document.pdf - Page 2"],
        "session_id": "uuid",
        "message_id": 1
    }
    """
    serializer = ChatRequestSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Get or create session
    session_id = serializer.validated_data.get('session_id')
    user_message = serializer.validated_data.get('user_message')

    try:
        if session_id:
            session = ChatSession.objects.get(session_id=session_id)
        else:
            session = ChatSession.objects.create()
            session_id = session.session_id

    except ChatSession.DoesNotExist:
        session = ChatSession.objects.create()
        session_id = session.session_id

    # Save user message
    user_msg_obj = Message.objects.create(
        session=session,
        message_type='user',
        content=user_message
    )

    # Get chat history for context
    chat_history = list(session.messages.exclude(id=user_msg_obj.id).values('message_type', 'content').order_by('-created_at'))
    chat_history = [{'type': msg['message_type'], 'content': msg['content']} for msg in chat_history]

    # Get RAG system and generate response
    rag_system = get_rag_system()

    try:
        answer, sources = rag_system.chat(user_message, chat_history)
    except Exception as e:
        return Response(
            {"error": f"Error generating response: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Save AI message
    ai_msg_obj = Message.objects.create(
        session=session,
        message_type='assistant',
        content=answer,
        sources=sources
    )

    # Return response
    response_data = {
        'answer': answer,
        'sources': sources,
        'session_id': str(session_id),
        'message_id': ai_msg_obj.id
    }

    return Response(response_data, status=status.HTTP_200_OK)


def _stream_chat_generator(session, user_message, user_msg_obj):
    """Generator that yields SSE events for streaming chat."""
    chat_history = list(
        session.messages.exclude(id=user_msg_obj.id)
        .values("message_type", "content")
        .order_by("-created_at")
    )
    chat_history = [
        {"type": msg["message_type"], "content": msg["content"]}
        for msg in chat_history
    ]

    rag_system = get_rag_system()
    full_answer = []

    try:
        for event in rag_system.chat_stream(user_message, chat_history):
            if not isinstance(event, tuple) or len(event) != 2:
                continue
            kind, value = event
            if kind == "chunk":
                full_answer.append(value)
                yield f"data: {json.dumps({'t': 'chunk', 'content': value})}\n\n"
            elif kind == "done":
                sources = value
                ai_msg_obj = Message.objects.create(
                    session=session,
                    message_type="assistant",
                    content="".join(full_answer),
                    sources=sources,
                )
                yield f"data: {json.dumps({'t': 'done', 'sources': sources, 'message_id': ai_msg_obj.id})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'t': 'error', 'error': str(e)})}\n\n"


@api_view(["POST"])
def chat_stream_endpoint(request):
    """
    Streaming chat: POST with session_id, user_message.
    Response: SSE stream of data: {"t": "chunk", "content": "..."} then {"t": "done", "sources": [...], "message_id": 1}.
    """
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    session_id = serializer.validated_data.get("session_id")
    user_message = serializer.validated_data.get("user_message")

    try:
        if session_id:
            session = ChatSession.objects.get(session_id=session_id)
        else:
            session = ChatSession.objects.create()
    except ChatSession.DoesNotExist:
        session = ChatSession.objects.create()

    user_msg_obj = Message.objects.create(
        session=session,
        message_type="user",
        content=user_message,
    )

    response = StreamingHttpResponse(
        _stream_chat_generator(session, user_message, user_msg_obj),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


@api_view(['GET'])
def get_session(request, session_id):
    """Get chat session with all messages"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        serializer = ChatSessionSerializer(session)
        return Response(serializer.data)
    except ChatSession.DoesNotExist:
        return Response(
            {"error": "Session not found"},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def create_session(request):
    """Create a new chat session"""
    session = ChatSession.objects.create()
    return Response({"session_id": str(session.session_id)}, status=status.HTTP_201_CREATED)
