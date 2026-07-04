"""Unit tests for the rule engine (open/resolve lifecycle, cooldown, timers)."""

from src.detection.types import Detection
from src.rules.engine import RuleEngine
from src.rules.types import Rule, Zone

ZONE = Zone(id="z1", polygon=[(0, 0), (100, 0), (100, 100), (0, 100)])


def _person(x: float, track_id: int) -> Detection:
    # foot point at (x, 50) — inside the zone
    return Detection(0, "person", 0.9, (x - 5, 40, x + 5, 50), track_id=track_id)


def _queue_rule() -> Rule:
    return Rule(
        id="r1", camera_id="cam1", rule_type="queue_threshold", zone_id="z1",
        severity="high", cooldown_seconds=300, config={"threshold": 2},
    )


def test_queue_opens_and_resolves() -> None:
    engine = RuleEngine()
    zones = {"z1": ZONE}
    rule = _queue_rule()

    # 3 people > threshold 2 -> OPEN
    people = [_person(10, 1), _person(30, 2), _person(50, 3)]
    events = engine.evaluate("cam1", people, [rule], zones, now=0.0)
    assert len(events) == 1
    assert events[0].event_type == "queue_threshold_exceeded"
    assert events[0].status == "open"

    # Still exceeded -> no duplicate event
    assert engine.evaluate("cam1", people, [rule], zones, now=1.0) == []

    # Drops to 1 -> RESOLVED
    events = engine.evaluate("cam1", [_person(10, 1)], [rule], zones, now=2.0)
    assert len(events) == 1
    assert events[0].event_type == "queue_resolved"
    assert events[0].status == "resolved"


def test_queue_cooldown_suppresses_reopen() -> None:
    engine = RuleEngine()
    zones = {"z1": ZONE}
    rule = _queue_rule()
    many = [_person(10, 1), _person(30, 2), _person(50, 3)]

    engine.evaluate("cam1", many, [rule], zones, now=0.0)  # open
    engine.evaluate("cam1", [_person(10, 1)], [rule], zones, now=1.0)  # resolve -> cooldown until 301

    # Re-exceed during cooldown -> suppressed
    assert engine.evaluate("cam1", many, [rule], zones, now=100.0) == []
    # After cooldown -> opens again
    events = engine.evaluate("cam1", many, [rule], zones, now=302.0)
    assert len(events) == 1 and events[0].status == "open"


def test_loitering_fires_after_threshold() -> None:
    engine = RuleEngine()
    zones = {"z1": ZONE}
    rule = Rule(
        id="r2", camera_id="cam1", rule_type="loitering", zone_id="z1",
        cooldown_seconds=300, config={"threshold_seconds": 60},
    )
    person = [_person(50, 7)]

    assert engine.evaluate("cam1", person, [rule], zones, now=0.0) == []  # just entered
    assert engine.evaluate("cam1", person, [rule], zones, now=59.0) == []  # not yet
    events = engine.evaluate("cam1", person, [rule], zones, now=61.0)  # over threshold
    assert len(events) == 1 and events[0].event_type == "loitering_detected"

    # Person leaves -> resolved
    events = engine.evaluate("cam1", [], [rule], zones, now=70.0)
    assert len(events) == 1 and events[0].event_type == "loitering_ended"


def test_unattended_counter() -> None:
    engine = RuleEngine()
    zones = {"z1": ZONE}
    rule = Rule(
        id="r3", camera_id="cam1", rule_type="unattended_billing_counter", zone_id="z1",
        cooldown_seconds=300, config={"threshold_seconds": 30},
    )

    assert engine.evaluate("cam1", [], [rule], zones, now=0.0) == []  # empty starts timer
    events = engine.evaluate("cam1", [], [rule], zones, now=31.0)  # empty > 30s
    assert len(events) == 1 and events[0].event_type == "unattended_billing_counter"

    events = engine.evaluate("cam1", [_person(50, 1)], [rule], zones, now=40.0)  # staffed
    assert len(events) == 1 and events[0].event_type == "billing_counter_staffed"
