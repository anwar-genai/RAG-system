import logging
import uuid

from django.http import JsonResponse

logger = logging.getLogger(__name__)

_BLOCKED_AGENTS = ('sqlmap', 'nikto', 'burpsuite', 'dirbuster', 'masscan', 'nmap')
_MAX_BODY_BYTES = 16 * 1024  # 16 KB — enforced for JSON endpoints only


class RequestIdMiddleware:
    """Tag every request with a short id, expose it as request.id and X-Request-ID."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = request.META.get('HTTP_X_REQUEST_ID') or uuid.uuid4().hex[:12]
        request.id = rid
        if request.path.startswith('/api/'):
            logger.info('rid=%s %s %s', rid, request.method, request.path)
        response = self.get_response(request)
        response['X-Request-ID'] = rid
        return response


class PromptGuardMiddleware:
    """Lightweight request guard: blocks scanner UAs, enforces body size limit, rejects null bytes."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith('/api/'):
            return self.get_response(request)

        ua = request.META.get('HTTP_USER_AGENT', '').lower()
        if any(agent in ua for agent in _BLOCKED_AGENTS):
            return JsonResponse({'error': 'Forbidden'}, status=403)

        # Skip body-size and null-byte checks for file uploads (multipart/form-data)
        # — Django's file upload system handles those separately with FILE_UPLOAD_MAX_MEMORY_SIZE.
        content_type = request.META.get('CONTENT_TYPE', '')
        is_multipart = content_type.startswith('multipart/form-data')

        if not is_multipart:
            content_length = int(request.META.get('CONTENT_LENGTH') or 0)
            if content_length > _MAX_BODY_BYTES:
                return JsonResponse({'error': 'Request body too large'}, status=413)

            if b'\x00' in request.body:
                return JsonResponse({'error': 'Invalid request'}, status=400)

        return self.get_response(request)
