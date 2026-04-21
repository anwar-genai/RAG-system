from django.http import JsonResponse

_BLOCKED_AGENTS = ('sqlmap', 'nikto', 'burpsuite', 'dirbuster', 'masscan', 'nmap')
_MAX_BODY_BYTES = 16 * 1024  # 16 KB


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

        content_length = int(request.META.get('CONTENT_LENGTH') or 0)
        if content_length > _MAX_BODY_BYTES:
            return JsonResponse({'error': 'Request body too large'}, status=413)

        if b'\x00' in request.body:
            return JsonResponse({'error': 'Invalid request'}, status=400)

        return self.get_response(request)
