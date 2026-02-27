"""
LINE Messaging API webhook handler.

Verifies the X-Line-Signature header and processes follow/unfollow events
to maintain CustomerLineBinding records.
"""

import logging

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def line_webhook(request):
    """Receive and process LINE webhook events."""
    channel_secret = getattr(settings, "LINE_CHANNEL_SECRET", "")
    if not channel_secret:
        return HttpResponse("LINE not configured", status=503)

    signature = request.META.get("HTTP_X_LINE_SIGNATURE", "")
    body = request.body.decode("utf-8")

    try:
        from linebot.v3 import WebhookParser
        from linebot.v3.exceptions import InvalidSignatureError
        from linebot.v3.webhooks.models import FollowEvent, UnfollowEvent

        parser = WebhookParser(channel_secret)
        try:
            events = parser.parse(body, signature)
        except InvalidSignatureError:
            logger.warning("LINE webhook: invalid signature")
            return HttpResponse("Invalid signature", status=400)

        for event in events:
            line_user_id = event.source.user_id if event.source else None
            if not line_user_id:
                continue

            if isinstance(event, FollowEvent):
                _handle_follow(line_user_id)
            elif isinstance(event, UnfollowEvent):
                _handle_unfollow(line_user_id)

    except Exception as exc:
        logger.exception("LINE webhook processing error: %s", exc)
        return HttpResponse("Error", status=500)

    return HttpResponse("OK")


def _handle_follow(line_user_id):
    """Create or restore a CustomerLineBinding when user follows the bot."""
    from .models import CustomerLineBinding

    CustomerLineBinding.objects.get_or_create(line_user_id=line_user_id)
    logger.info("LINE follow: %s", line_user_id)


def _handle_unfollow(line_user_id):
    """Remove CustomerLineBinding when user blocks/unfollows the bot."""
    from .models import CustomerLineBinding

    CustomerLineBinding.objects.filter(line_user_id=line_user_id).delete()
    logger.info("LINE unfollow: %s", line_user_id)
