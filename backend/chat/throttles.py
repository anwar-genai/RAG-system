from rest_framework.throttling import UserRateThrottle


class ChatRateThrottle(UserRateThrottle):
    scope = 'chat'


class UploadRateThrottle(UserRateThrottle):
    scope = 'upload'
