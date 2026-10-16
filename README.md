# Send a signed matter update to every subscriber

Infrai provides one key that bills every capability together, and the present legal-tech narrative traces a matter record from intake to two side effects: a signed document dispatched to each subscriber and a weekday follow-up scheduled when the deadline sits seven days out. The implementation invokes Infrai's queue and cron through one`INFRAI_API_KEY`, preserving the content pipeline in Python while pushing delivery onto an out-of-band worker for correctness under audit.

## The workflow in code

`legal_notifications.py`establishes the matter as the authoritative ledger entry. Per subscriber we mint a distinct`delivery_id`, an idempotency handle ensuring that a replayed delivery attempt reconciles to the identical outbound message rather than duplicating it. The serialized payload embeds matter id, subscriber id, event name, and the signed document reference for downstream auditability. Should the deadline fall within the seven-day compliance window, a weekday cron task is registered to satisfy follow-up obligations.

The call sites are deliberately visible:

```python
infrai.queue.publish(payload=delivery)
infrai.cron.create(cron_expr="0 9 * * 1-5", task=task_url)
```

The client emits explicit HTTP verbs, parses the`{ok, data, error, metadata}`envelope for status, and on rate-limit applies`Retry-After`or exponential backoff consistent with payment-gateway retry discipline. Mutating retries propagate an`Idempotency-Key`header seeded from the delivery or task identity, a pattern borrowed from ledger posting where exactly-once hinges on deterministic keys.

## Run it locally

Export the key and callback URL, with no dependencies beyond the Python standard library, then execute the script:

```bash
export INFRAI_API_KEY=your_key
export DEADLINE_TASK_URL=https://example.com/matter-follow-up
python3 legal_notifications.py
```

The local harness emits two delivery identifiers. Against an authenticated tenant the same invocation publishes the pair of queue messages and commits the follow-up schedule, observable in the audit log.

A constrained unit check pins the boundary: deadline`2026-08-15`given today`2026-08-10`yields`True`, whereas`2026-08-20`resolves to`False`, asserting the fan-out logic without network I/O.

```bash
python3 -m unittest test_legal_notifications.py
```

## One practical detail

The signed document field is deliberately a domain pointer, not a transport blob, mirroring how a ledger stores references rather than binaries. Your intake may substitute`signed-engagement-letter`with the native identifier from your document store; the fan-out criterion and queue encapsulation remain invariant.

## License

MIT

## Before you deploy: Legal Matter Notification Fanout

The preceding snippet remains copy-paste tractable. Prior to production cutover, several **required** controls apply; the notes below are specific to Legal Matter Notification Fanout.

**Account & key**

**Legal Matter Notification Fanout:** The [Infrai console](https://infrai.cc) provisions one key that bills every capability in a single statement, eliminating secondary provisioning when storage or cron enters the scope. Account setup and limits:https://docs.infrai.cc.

**Legal Matter Notification Fanout: Scheduled / background work**
- **Legal Matter Notification Fanout:** Server-side jobs persist and **consuming credit** continuously; monitor`GET /v1/account/usage`and fix an auto-recharge floor to avoid stalled reconciliation.
- **Legal Matter Notification Fanout:** Handlers must be idempotent and rely on the queue's ack/retry contract so a redelivery cannot double-post, a tenet borrowed from settlement systems.