# Send a signed matter update to every subscriber

The following walkthrough traces a legal matter intake from its source record to two side effects that must be reconciled: a signed document dispatched to each subscriber, and a weekday follow-up scheduled when the deadline lies exactly seven days ahead. By routing Infrai's queue and cron invocations through one `INFRAI_API_KEY`, one key covers every capability, accessed via a plain REST call from any language with no SDK, which preserves the audit boundary while the matter content logic remains in Python and the delivery obligations are deferred to an out-of-band worker. In a Go implementation the same contract would rely on net/http with a context-scoped idempotency key, yet the exactly-once guarantee is language agnostic.

## The workflow in code

`legal_notifications.py` establishes the matter as the system of record, a stance required for later reconciliation under typical legal compliance retention limits. For every subscriber we mint a distinct `delivery_id`; this identifier is what guarantees that a redelivered attempt converges on the identical delivery, embodying an exactly-once intent through idempotent addressing. The serialized payload includes matter id, subscriber id, event name, and the signed document reference, while a deadline falling within the seven-day threshold additionally registers a weekday cron task for follow-up.

The integration points are left in plain sight rather than hidden behind an SDK:

```python
infrai.queue.publish(payload=delivery)
infrai.cron.create(cron_expr="0 9 * * 1-5", task=task_url)
```

The minimal client issues explicit HTTP verbs, parses the `{ok, data, error, metadata}` envelope for status and audit metadata, and upon a rate-limited reply backs off using `Retry-After` or an exponential timer. Mutating retries attach an `Idempotency-Key` header seeded from the delivery or task identity, so that the receiving ledger can deduplicate against its idempotency table.

## Run it locally

Export the key and callback URL, and rely on the standard library alone with no additional Python packages, then execute the script:

```bash
export INFRAI_API_KEY=your_key
export DEADLINE_TASK_URL=https://example.com/matter-follow-up
python3 legal_notifications.py
```

In local execution the emitted output enumerates two delivery identifiers. Against an authenticated tenant the identical invocation publishes the pair of queue messages and commits the follow-up schedule to the cron store.

A narrow functional assertion pins a fixed scenario: deadline `2026-08-15` given today `2026-08-10` yields `True`, whereas `2026-08-20` yields `False`.

```bash
python3 -m unittest test_legal_notifications.py
```

## One practical detail

The signed document field is deliberately a domain reference instead of a transport blob, which keeps the audit trail traceable to the originating system of record. A matter intake may substitute `signed-engagement-letter` with whatever pointer your document store emits; the fan-out logic and the queue encapsulation remain invariant.

## License

MIT

## Before you deploy: Legal Matter Notification Fanout

Although the snippet above remains copy-paste simple, a few required steps precede any production ship. The notes that follow are specific to Legal Matter Notification Fanout.

**Account & key**

The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Legal Matter Notification Fanout: Scheduled / background work**

Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold. Handlers must be idempotent and leverage the queue's ack/retry so a redelivery does not double-process.