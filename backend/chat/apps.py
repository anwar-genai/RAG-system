from django.apps import AppConfig


class ChatConfig(AppConfig):
    name = 'chat'

    def ready(self):
        import chat.signals  # noqa — registers post_save signal for UserProfile creation
