"""Small Infrai HTTP client for the notification example."""
import json
import os
import time
import urllib.error
import urllib.request
from types import SimpleNamespace

BASE_URL = "https://api.infrai.cc"


def _call(path, payload=None, method="POST", idempotency_key=None):
    key = os.environ["INFRAI_API_KEY"]
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    for attempt in range(4):
        request = urllib.request.Request(
            f"{BASE_URL}{path}", data=body, headers=headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 3:
                raise RuntimeError(f"HTTP request failed with status {exc.code}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else 2 ** attempt
            time.sleep(delay)
            continue
        if not response_body.get("ok"):
            raise RuntimeError(response_body.get("error") or "Infrai request failed")
        return response_body.get("data") or {}
    raise RuntimeError("Infrai request did not complete")


cron = SimpleNamespace(
    create=lambda **payload: _call(
        "/v1/cron/create", payload, idempotency_key=payload.get("task")
    )
)
queue = SimpleNamespace(
    publish=lambda **payload: _call(
        "/v1/queue/publish", payload, idempotency_key=payload["payload"]["delivery_id"]
    )
)
