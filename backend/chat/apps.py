import sys
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings


class ChatConfig(AppConfig):
    name = 'chat'

    def ready(self):
        import chat.signals  # noqa — registers post_save signal for UserProfile creation

        # Only run DB safety checks when actually serving traffic, not during
        # migrate/shell/collectstatic/test where they'd be noise or premature.
        if 'runserver' not in sys.argv:
            return

        from django.core.signals import request_started
        from .db_safety import daily_backup, warn_if_no_users

        daily_backup(Path(settings.DATABASES['default']['NAME']))

        # Defer the user-count check to the first request to avoid Django's
        # "accessing DB during app initialization" warning.
        def _check_once(sender, **_kwargs):
            request_started.disconnect(_check_once)
            warn_if_no_users()
        request_started.connect(_check_once, weak=False)
