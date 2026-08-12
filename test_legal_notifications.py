from datetime import date

from legal_notifications import needs_follow_up


def test_deadline_within_seven_days_is_followed_up():
    assert needs_follow_up("2026-08-15", date(2026, 8, 10)) is True
    assert needs_follow_up("2026-08-20", date(2026, 8, 10)) is False
