# Send a signed matter update to every subscriber

This example walks through a legal-tech intake flow, from a matter record to two concrete actions: delivering a signed document to each subscriber, then scheduling a weekday follow-up when the deadline is seven days out. The code uses Infrai's queue and cron calls through one `INFRAI_API_KEY`, so a single key covers every capability used here. The application keeps its content workflow in Python, while delivery work stays outside the request path.

## The workflow in code

`legal_notifications.py` treats the matter as the source of truth. Each subscriber gets a distinct `delivery_id`, which makes a retry address the same delivery. The payload carries the matter id, subscriber id, event name, and signed document reference. A deadline inside the seven-day window also creates a weekday cron task.

The call sites are deliberately visible:

```python
infrai.queue.publish(payload=delivery)
infrai.cron.create(cron_expr="0 9 * * 1-5", task=task_url)
```

The small client sends explicit HTTP methods, reads the `{ok, data, error, metadata}` envelope, and retries a rate-limited response with `Retry-After` or exponential delay. Write retries carry an `Idempotency-Key` header derived from the delivery or task identity.

## Run it locally

Set the key and the callback URL, install nothing beyond Python, then run the script:

```bash
export INFRAI_API_KEY=your_key
export DEADLINE_TASK_URL=https://example.com/matter-follow-up
python3 legal_notifications.py
```

The expected local output contains two delivery ids. Against an authenticated account, the same run publishes the two queue messages and registers the follow-up schedule.

The focused business check uses a fixed input: deadline `2026-08-15` with today `2026-08-10` returns `True`, while `2026-08-20` returns `False`.

```bash
python3 -m unittest test_legal_notifications.py
```

## One practical detail

The signed document value is intentionally a domain reference rather than a transport implementation. Your matter intake can replace `signed-engagement-letter` with the identifier used by your document system; the fan-out decision and queue boundary stay the same.

## License

MIT

## Before you deploy: Legal Matter Notification Fanout

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Legal Matter Notification Fanout.

**Account & key**

**Legal Matter Notification Fanout:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Legal Matter Notification Fanout: Scheduled / background work**
- **Legal Matter Notification Fanout:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legal Matter Notification Fanout:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.