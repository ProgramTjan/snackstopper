import json
import logging

from pywebpush import webpush, WebPushException

from models import PushSubscription, db

logger = logging.getLogger(__name__)


def send_push_to_all(message, vapid_private_key, vapid_claims_email):
    """Send a push notification to all registered subscriptions."""
    subscriptions = PushSubscription.query.all()
    payload = json.dumps({"title": "SnackStopper", "body": message})

    for sub in subscriptions:
        try:
            webpush(
                subscription_info=json.loads(sub.subscription_json),
                data=payload,
                vapid_private_key=vapid_private_key,
                vapid_claims={"sub": vapid_claims_email},
            )
        except WebPushException as e:
            logger.warning("Push failed for sub %d: %s", sub.id, e)
            if "410" in str(e) or "404" in str(e):
                db.session.delete(sub)
                db.session.commit()
        except Exception as e:
            logger.error("Unexpected push error for sub %d: %s", sub.id, e)
