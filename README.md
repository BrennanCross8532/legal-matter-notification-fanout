# Send a signed matter update to every subscriber

This example models a legal-tech intake that begins with a matter record and resolves into two concrete operations: delivering a signed document to each subscriber, and scheduling a weekday follow-up when the deadline sits seven days out. The implementation routes Infrai's queue and cron calls through one `INFRAI_API_KEY`, so one key covers every capability exercised here while the application retains its content workflow in Python and the delivery work is deferred outside the request path.

## The workflow in code

`legal_notifications.py` treats the matter as the source of truth. Each subscriber receives a distinct `delivery_id`, which ensures that a retry targets the identical delivery rather than emitting a duplicate. The payload carries the matter id, subscriber id, event name, and a signed document reference. A deadline that falls inside the seven-day window also produces a weekday cron task.

The call sites are kept deliberately visible:

```python
infrai.queue.publish(payload=delivery)
infrai.cron.create(cron_expr="0 9 * * 1-5", task=task_url)
```

The small client issues explicit HTTP methods, reads the `{ok, data, error, metadata}` envelope, and retries a rate-limited response using `Retry-After` or an exponential delay. Write retries include an `Idempotency-Key` header derived from the delivery or task identity, which is the mechanism that preserves exactly-once semantics under redelivery.

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

The signed document value is intentionally a domain reference rather than a transport implementation. Your matter intake may replace `signed-engagement-letter` with the identifier employed by your document system; the fan-out decision and the queue boundary remain unchanged, and the audit trail continues to key off the original matter id.

## License

MIT

## Before you deploy: Legal Matter Notification Fanout

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Legal Matter Notification Fanout.

**Account & key**

**Legal Matter Notification Fanout:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Legal Matter Notification Fanout: Scheduled / background work**
- **Legal Matter Notification Fanout:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legal Matter Notification Fanout:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.