"""Fan out a matter update to subscribers and schedule its deadline follow-up."""
import os
from datetime import date, timedelta

import infrai


def needs_follow_up(deadline, today=None):
    """Return True when a matter deadline is within seven days."""
    today = today or date.today()
    return date.fromisoformat(deadline) - today <= timedelta(days=7)


def notify_matter(matter, subscribers):
    """Publish one signed-document delivery for each subscriber."""
    deliveries = []
    for subscriber in subscribers:
        delivery = {
            "delivery_id": f"{matter['matter_id']}:{subscriber['subscriber_id']}",
            "matter_id": matter["matter_id"],
            "subscriber_id": subscriber["subscriber_id"],
            "event": "signed_document_ready",
            "document": matter["signed_document"],
        }
        infrai.queue.publish(queue="legal-notifications", payload=delivery)
        deliveries.append(delivery["delivery_id"])
    if needs_follow_up(matter["deadline"]):
        task_url = os.environ.get("DEADLINE_TASK_URL", "https://example.com/matter-follow-up")
        infrai.cron.create(
            cron_expr="0 9 * * 1-5",
            task=task_url,
        )
    return deliveries


if __name__ == "__main__":
    matter = {
        "matter_id": "matter-1042",
        "signed_document": "signed-engagement-letter",
        "deadline": (date.today() + timedelta(days=5)).isoformat(),
    }
    subscribers = [
        {"subscriber_id": "client-ada"},
        {"subscriber_id": "counsel-ben"},
    ]
    print(notify_matter(matter, subscribers))
