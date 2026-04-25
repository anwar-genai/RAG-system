import json
import os
from pathlib import Path
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import ChatSession, Message, KnowledgeDocument
from .serializers import ChatRequestSerializer, ChatSessionSerializer
from .rag import get_rag_system, reload_rag_system, UpstreamUnavailable, GENERIC_ERROR_MSG
from .sanitizers import sanitize_message
from .moderation import is_content_safe
from .throttles import ChatRateThrottle, UploadRateThrottle
from .permissions import IsAdminRole


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_session(session_id, user):
    if session_id:
        try:
            return ChatSession.objects.get(session_id=session_id, user=user)
        except ChatSession.DoesNotExist:
            pass
    return ChatSession.objects.create(user=user)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    if len(username) < 3:
        return Response({"error": "Username must be at least 3 characters."}, status=status.HTTP_400_BAD_REQUEST)
    if len(password) < 8:
        return Response({"error": "Password must be at least 8 characters."}, status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username is already taken."}, status=status.HTTP_400_BAD_REQUEST)

    # Profile (and admin-promotion for first user) is created by the post_save signal in signals.py.
    User.objects.create_user(username=username, password=password)
    return Response({"message": "Account created. You can now sign in."}, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return the current user's id, username, and role.
    Self-heals two pre-existing-user cases:
      1. No UserProfile yet → create one.
      2. No admin exists system-wide → promote the caller (first-user-wins rule)."""
    from .models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={"role": "user"},
    )

    # If the system has zero admins, promote the caller so the app is always administrable.
    if not UserProfile.objects.filter(role="admin").exists():
        profile.role = "admin"
        profile.save(update_fields=["role"])

    return Response({
        "id": request.user.id,
        "username": request.user.username,
        "role": profile.role,
        "date_joined": request.user.date_joined,
    })


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([ChatRateThrottle])
def chat_endpoint(request):
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    session_id = serializer.validated_data.get('session_id')
    user_message = serializer.validated_data.get('user_message')

    is_safe, result = sanitize_message(user_message)
    if not is_safe:
        return Response({"error": result}, status=status.HTTP_400_BAD_REQUEST)
    user_message = result

    if not is_content_safe(user_message)[0]:
        return Response({"error": "Message not allowed."}, status=status.HTTP_400_BAD_REQUEST)

    session = _get_or_create_session(session_id, request.user)
    user_msg_obj = Message.objects.create(session=session, message_type='user', content=user_message)

    chat_history = [
        {'type': m['message_type'], 'content': m['content']}
        for m in session.messages.exclude(id=user_msg_obj.id).values('message_type', 'content').order_by('created_at')
    ]

    rag_system = get_rag_system()
    rid = getattr(request, 'id', '')
    try:
        answer, sources, usage = rag_system.chat(user_message, chat_history)
    except UpstreamUnavailable as e:
        return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception:
        return Response({"error": GENERIC_ERROR_MSG}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ai_msg_obj = Message.objects.create(
        session=session, message_type='assistant', content=answer, sources=sources,
        request_id=rid,
        tokens_in=usage.get('tokens_in'),
        tokens_out=usage.get('tokens_out'),
        cost_usd=usage.get('cost_usd'),
    )
    return Response({
        'answer': answer,
        'sources': sources,
        'session_id': str(session.session_id),
        'message_id': ai_msg_obj.id,
    })


def _extract_and_store_memories(rag_system, user_id, user_message, assistant_reply, ai_msg_obj):
    """Pull durable user facts from one exchange and persist to UserMemory + FAISS.
    Non-fatal — chat reply has already streamed, so any failure is swallowed."""
    if not user_id or not assistant_reply:
        return
    try:
        facts = rag_system.extract_memories(user_message, assistant_reply)
        if not facts:
            return
        from .models import UserMemory
        from .memory import get_memory_store
        store = get_memory_store()
        for fact in facts:
            mem = UserMemory.objects.create(
                user_id=user_id, content=fact, source='auto',
                source_message=ai_msg_obj,
            )
            # MemoryStore returns False on near-duplicate; drop the orphan DB row
            # so it doesn't accumulate as the user re-mentions the same fact.
            if not store.add(user_id, fact, mem.id):
                mem.delete()
    except Exception:
        import traceback
        traceback.print_exc()


def _stream_chat_generator(session, user_message, user_msg_obj, request_id='', user_id=None):
    chat_history = [
        {"type": m["message_type"], "content": m["content"]}
        for m in session.messages.exclude(id=user_msg_obj.id).values("message_type", "content").order_by("created_at")
    ]

    rag_system = get_rag_system()
    full_answer = []
    usage: dict = {}
    ai_msg_obj = None
    errored = False

    try:
        for event in rag_system.chat_stream(user_message, chat_history, user_id=user_id):
            if not isinstance(event, tuple) or len(event) != 2:
                continue
            kind, value = event
            if kind == "chunk":
                full_answer.append(value)
                yield f"data: {json.dumps({'t': 'chunk', 'content': value})}\n\n"
            elif kind == "usage":
                usage = value or {}
            elif kind == "done":
                ai_msg_obj = Message.objects.create(
                    session=session, message_type="assistant",
                    content="".join(full_answer), sources=value,
                    request_id=request_id,
                    tokens_in=usage.get('tokens_in'),
                    tokens_out=usage.get('tokens_out'),
                    cost_usd=usage.get('cost_usd'),
                )
                # Auto-title on the first assistant reply (exactly 2 messages after save).
                # Failure is non-fatal — the sidebar falls back to the message preview.
                if not session.title and session.messages.count() == 2:
                    title = rag_system.generate_title(user_message, "".join(full_answer))
                    if title:
                        ChatSession.objects.filter(pk=session.pk).update(title=title)
                        session.title = title
                yield f"data: {json.dumps({'t': 'done', 'sources': value, 'message_id': ai_msg_obj.id, 'session_id': str(session.session_id), 'title': session.title})}\n\n"
                _extract_and_store_memories(
                    rag_system, user_id, user_message,
                    "".join(full_answer), ai_msg_obj,
                )
            elif kind == "error":
                errored = True
                yield f"data: {json.dumps({'t': 'error', 'error': value})}\n\n"
    except Exception:
        errored = True
        yield f"data: {json.dumps({'t': 'error', 'error': GENERIC_ERROR_MSG})}\n\n"
    finally:
        # Only persist a partial assistant message if we actually got some content
        # AND we didn't error out. On error, don't save a half-baked reply.
        if full_answer and ai_msg_obj is None and not errored:
            Message.objects.create(
                session=session, message_type="assistant", content="".join(full_answer), sources=[],
                request_id=request_id,
                tokens_in=usage.get('tokens_in'),
                tokens_out=usage.get('tokens_out'),
                cost_usd=usage.get('cost_usd'),
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ChatRateThrottle])
def chat_stream_endpoint(request):
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    session_id = serializer.validated_data.get("session_id")
    user_message = serializer.validated_data.get("user_message")

    is_safe, result = sanitize_message(user_message)
    if not is_safe:
        return Response({"error": result}, status=status.HTTP_400_BAD_REQUEST)
    user_message = result

    if not is_content_safe(user_message)[0]:
        return Response({"error": "Message not allowed."}, status=status.HTTP_400_BAD_REQUEST)

    session = _get_or_create_session(session_id, request.user)
    rid = getattr(request, 'id', '')
    user_msg_obj = Message.objects.create(
        session=session, message_type="user", content=user_message, request_id=rid,
    )

    response = StreamingHttpResponse(
        _stream_chat_generator(session, user_message, user_msg_obj, request_id=rid, user_id=request.user.id),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    response["X-Request-ID"] = rid
    return response


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def message_feedback(request, message_id):
    """Set thumbs-up/down on an assistant message owned by the caller."""
    mapping = {"up": 1, "down": -1, "clear": 0, None: 0}
    vote = request.data.get("vote")
    if vote not in mapping:
        return Response({"error": "vote must be 'up', 'down', or 'clear'"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        msg = Message.objects.get(
            pk=message_id, session__user=request.user, message_type='assistant',
        )
    except Message.DoesNotExist:
        return Response({"error": "Message not found"}, status=status.HTTP_404_NOT_FOUND)
    msg.feedback = mapping[vote]
    msg.save(update_fields=['feedback'])
    return Response({"id": msg.id, "feedback": msg.feedback})


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def get_session(request, session_id):
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)
    except ChatSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(ChatSessionSerializer(session).data)

    if request.method == 'DELETE':
        session.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # PATCH — rename or pin toggle
    changed = False
    if 'title' in request.data:
        title = (request.data.get('title') or '').strip()[:120]
        if title != session.title:
            session.title = title
            changed = True
    if 'pinned' in request.data:
        pinned = bool(request.data.get('pinned'))
        if pinned != session.pinned:
            session.pinned = pinned
            changed = True
    if changed:
        # Don't bump updated_at for pin toggles or renames — preserves sort order
        ChatSession.objects.filter(pk=session.pk).update(
            title=session.title, pinned=session.pinned,
        )
    return Response({
        "session_id": str(session.session_id),
        "title": session.title,
        "pinned": session.pinned,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sessions(request):
    """List all non-empty sessions for the current user, newest first.
    Empty sessions (user opened a new chat but never sent a message) are hidden —
    they'd otherwise pile up as identical 'New conversation' entries in the sidebar."""
    sessions = (
        ChatSession.objects.filter(user=request.user)
        .annotate(message_count=Count('messages'))
        .filter(message_count__gt=0)
        .order_by('-pinned', '-updated_at')
    )

    data = []
    for s in sessions:
        if s.title:
            title = s.title
        else:
            first_msg = s.messages.filter(message_type='user').order_by('created_at').first()
            if first_msg:
                title = first_msg.content[:60] + ('…' if len(first_msg.content) > 60 else '')
            else:
                title = 'New conversation'
        data.append({
            "session_id": str(s.session_id),
            "title": title,
            "pinned": s.pinned,
            "message_count": s.message_count,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session(request):
    session = ChatSession.objects.create(user=request.user)
    return Response({"session_id": str(session.session_id)}, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Document upload
# ---------------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminRole])
@throttle_classes([UploadRateThrottle])
def upload_documents(request):
    uploaded_files = request.FILES.getlist("files") or ([request.FILES["file"]] if "file" in request.FILES else [])

    if not uploaded_files:
        return Response({"error": "No files uploaded. Use field 'files'."}, status=status.HTTP_400_BAD_REQUEST)

    allowed_exts = {".pdf", ".txt", ".md", ".docx", ".csv"}
    kb_path = Path(__file__).parent.parent / "knowledge_base"
    kb_path.mkdir(exist_ok=True)

    saved, skipped = [], []

    for up_file in uploaded_files:
        ext = os.path.splitext(up_file.name)[1].lower()
        if ext not in allowed_exts:
            skipped.append({"name": up_file.name, "reason": "unsupported file type"})
            continue

        safe_name = Path(up_file.name).name
        target_path = kb_path / safe_name
        with target_path.open("wb") as out:
            for chunk in up_file.chunks():
                out.write(chunk)

        # Track in DB
        KnowledgeDocument.objects.update_or_create(
            name=safe_name,
            defaults={
                "file_type": ext.lstrip(".").upper(),
                "size_bytes": target_path.stat().st_size,
                "uploaded_by": request.user,
                "status": "indexed",
            },
        )
        saved.append(safe_name)

    if not saved:
        return Response({"error": "No supported files uploaded.", "skipped": skipped}, status=status.HTTP_400_BAD_REQUEST)

    try:
        rag = reload_rag_system()
    except Exception as e:
        KnowledgeDocument.objects.filter(name__in=saved).update(status="failed")
        return Response(
            {"error": f"Files uploaded but failed to refresh index: {e}", "uploaded": saved, "skipped": skipped},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Reflect per-file indexing failures (parser errors, empty extractions) in the DB
    # so the admin UI shows "failed" instead of a misleading "indexed".
    failed = list(getattr(rag, "failed_files", []) or [])
    failed_names = {name for name, _ in failed}
    if failed_names:
        KnowledgeDocument.objects.filter(name__in=failed_names).update(status="failed")

    indexed = [n for n in saved if n not in failed_names]
    failed_for_saved = [{"name": n, "reason": r} for n, r in failed if n in set(saved)]

    return Response(
        {
            "uploaded": indexed,
            "failed": failed_for_saved,
            "skipped": skipped,
            "message": "Documents uploaded and index refreshed.",
        },
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminRole])
def admin_stats(_request):
    """System-wide overview stats for the admin dashboard."""
    kb_path = Path(__file__).parent.parent / "knowledge_base"

    kb_size = 0
    documents_by_type: dict[str, int] = {}
    if kb_path.exists():
        for f in kb_path.iterdir():
            if not f.is_file():
                continue
            kb_size += f.stat().st_size
            ext = f.suffix.lstrip(".").upper() or "OTHER"
            documents_by_type[ext] = documents_by_type.get(ext, 0) + 1

    return Response({
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "total_sessions": ChatSession.objects.count(),
        "total_messages": Message.objects.count(),
        "total_documents": KnowledgeDocument.objects.count(),
        "kb_size_bytes": kb_size,
        "documents_by_type": documents_by_type,
    })


# ---------------------------------------------------------------------------
# Eval results — surfaces evals/results/*.json to the admin dashboard so
# scores and cost are visible without SSH-ing in to cat the JSON.
# ---------------------------------------------------------------------------

_EVALS_RESULTS_DIR = Path(__file__).resolve().parent.parent.parent / "evals" / "results"
_REPORT_PDF_PATH = _EVALS_RESULTS_DIR / "Accuracy_Report.pdf"


def _read_json_safe(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminRole])
def admin_eval_results(_request):
    """Return the latest RAGAS + G-Eval result JSONs and whether the PDF is ready."""
    ragas = _read_json_safe(_EVALS_RESULTS_DIR / "ragas_results.json")
    geval = _read_json_safe(_EVALS_RESULTS_DIR / "geval_results.json")
    return Response({
        "ragas": ragas,
        "geval": geval,
        "pdf_available": _REPORT_PDF_PATH.exists(),
        "pdf_generated_at": (
            __import__("datetime").datetime.fromtimestamp(_REPORT_PDF_PATH.stat().st_mtime).isoformat(timespec="seconds")
            if _REPORT_PDF_PATH.exists() else None
        ),
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminRole])
def admin_eval_report_pdf(_request):
    """Stream the latest Accuracy_Report.pdf for admin download."""
    from django.http import FileResponse
    if not _REPORT_PDF_PATH.exists():
        return Response(
            {"error": "Report not generated yet. Run: python evals/run_all.py && python evals/report.py"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return FileResponse(
        _REPORT_PDF_PATH.open("rb"),
        as_attachment=True,
        filename="Accuracy_Report.pdf",
        content_type="application/pdf",
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminRole])
def admin_users(request):
    """List all users with session/message counts and role."""
    users = (
        User.objects.select_related("profile")
        .annotate(session_count=Count("sessions", distinct=True), message_count=Count("sessions__messages", distinct=True))
        .order_by("-date_joined")
    )
    data = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.profile.role if hasattr(u, "profile") else "user",
            "is_active": u.is_active,
            "date_joined": u.date_joined,
            "last_login": u.last_login,
            "session_count": u.session_count,
            "message_count": u.message_count,
        }
        for u in users
    ]
    return Response(data)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminRole])
def admin_user_detail(request, user_id):
    """Update (role/active) or delete a user. Cannot self-delete or demote last admin."""
    try:
        target = User.objects.select_related("profile").get(pk=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "DELETE":
        if target.pk == request.user.pk:
            return Response({"error": "You cannot delete your own account."}, status=status.HTTP_400_BAD_REQUEST)
        target.delete()
        return Response({"message": "User deleted."})

    # PATCH
    profile = getattr(target, "profile", None)
    new_role = request.data.get("role")
    new_active = request.data.get("is_active")

    if new_role and profile:
        if new_role not in ("admin", "user"):
            return Response({"error": "Role must be 'admin' or 'user'."}, status=status.HTTP_400_BAD_REQUEST)
        # Guard: cannot demote the last admin
        if new_role == "user" and profile.role == "admin":
            admin_count = User.objects.filter(profile__role="admin").count()
            if admin_count <= 1:
                return Response({"error": "Cannot demote the last admin."}, status=status.HTTP_400_BAD_REQUEST)
        profile.role = new_role
        profile.save()

    if new_active is not None:
        if target.pk == request.user.pk and not new_active:
            return Response({"error": "You cannot deactivate your own account."}, status=status.HTTP_400_BAD_REQUEST)
        target.is_active = bool(new_active)
        target.save()

    return Response({
        "id": target.pk,
        "username": target.username,
        "role": profile.role if profile else "user",
        "is_active": target.is_active,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminRole])
def admin_documents(_request):
    """List all knowledge base documents (DB records merged with filesystem)."""
    kb_path = Path(__file__).parent.parent / "knowledge_base"
    allowed_exts = {".pdf", ".txt", ".md", ".docx", ".csv"}

    # Filesystem is the source of truth for existence
    fs_files = {
        f.name: f for f in kb_path.iterdir()
        if f.is_file() and f.suffix.lower() in allowed_exts
    } if kb_path.exists() else {}

    db_records = {doc.name: doc for doc in KnowledgeDocument.objects.select_related("uploaded_by").all()}

    docs = []
    for name, path in fs_files.items():
        rec = db_records.get(name)
        docs.append({
            "name": name,
            "file_type": path.suffix.lstrip(".").upper(),
            "size_bytes": path.stat().st_size,
            "status": rec.status if rec else "indexed",
            "uploaded_by": rec.uploaded_by.username if rec and rec.uploaded_by else "system",
            "uploaded_at": rec.uploaded_at.isoformat() if rec else None,
        })

    docs.sort(key=lambda d: d["uploaded_at"] or "", reverse=True)
    return Response(docs)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdminRole])
def admin_document_delete(request, doc_name):
    """Delete a document from the knowledge base and rebuild the index."""
    kb_path = Path(__file__).parent.parent / "knowledge_base"

    # Reject any path separators / traversal segments up front — only a bare filename is allowed.
    if doc_name != Path(doc_name).name or doc_name in ("", ".", ".."):
        return Response({"error": "Invalid document name."}, status=status.HTTP_400_BAD_REQUEST)

    target = kb_path / doc_name

    # Defense in depth: ensure resolved target stays inside kb_path.
    try:
        target.resolve().relative_to(kb_path.resolve())
    except ValueError:
        return Response({"error": "Invalid document name."}, status=status.HTTP_400_BAD_REQUEST)

    if not target.exists() or not target.is_file():
        return Response({"error": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

    target.unlink()
    KnowledgeDocument.objects.filter(name=doc_name).delete()

    try:
        reload_rag_system()
    except Exception as e:
        return Response({"error": f"File deleted but index refresh failed: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({"message": f"'{doc_name}' deleted and index rebuilt."})
