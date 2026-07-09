"""The rule engine.

Given the current frame's detections plus a camera's rules and zones, produces
business events (OPEN/RESOLVED) while maintaining ephemeral temporal state.
Pure and deterministic given (detections, rules, zones, now) — fully testable.
"""

from __future__ import annotations

from src.detection.types import Detection
from src.rules.geometry import count_people_in_zone, foot_point, point_in_polygon, side_of_line
from src.rules.state import CameraState
from src.rules.types import BusinessEvent, Rule, Zone

# rule_type -> (open_event_type, resolved_event_type)
_COUNT_RULES = {
    "queue_threshold": ("queue_threshold_exceeded", "queue_resolved"),
    "occupancy_limit": ("occupancy_limit_exceeded", "occupancy_normalized"),
}


class RuleEngine:
    def __init__(self) -> None:
        self._state: dict[str, CameraState] = {}

    def evaluate(
        self,
        camera_id: str,
        detections: list[Detection],
        rules: list[Rule],
        zones: dict[str, Zone],
        now: float,
    ) -> list[BusinessEvent]:
        state = self._state.setdefault(camera_id, CameraState())
        persons = [d for d in detections if d.class_name == "person"]
        events: list[BusinessEvent] = []

        for rule in rules:
            # Line crossing uses a line from config, not a polygon zone.
            if rule.rule_type == "line_crossing":
                events += self._eval_line_crossing(state, rule, detections, now)
                continue

            zone = zones.get(rule.zone_id) if rule.zone_id else None
            if zone is None:
                continue
            if rule.rule_type in _COUNT_RULES:
                open_t, resolve_t = _COUNT_RULES[rule.rule_type]
                events += self._eval_count(state, rule, zone, persons, now, open_t, resolve_t)
            elif rule.rule_type == "loitering":
                events += self._eval_loitering(state, rule, zone, persons, now)
            elif rule.rule_type == "unattended_billing_counter":
                events += self._eval_unattended(state, rule, zone, persons, now)
            elif rule.rule_type == "intrusion":
                events += self._eval_intrusion(state, rule, zone, detections, now)
        return events

    # ----- intrusion (object enters a zone, per track) --------------------

    @staticmethod
    def _rule_classes(rule: Rule, default: tuple[str, ...]) -> set[str]:
        cfg = rule.config.get("classes")
        return set(cfg) if cfg else set(default)

    def _eval_intrusion(self, state, rule: Rule, zone: Zone, detections, now) -> list[BusinessEvent]:
        """Zone-breach intrusion: OPEN when any object of an allowed class is
        inside the zone, RESOLVE when the zone is clear again. Presence-based (no
        dependency on track ids, which are unreliable at low sample FPS). Class
        filter comes from ``config.classes`` (default: person)."""
        classes = self._rule_classes(rule, ("person",))
        intruders = [
            d
            for d in detections
            if d.class_name in classes and point_in_polygon(foot_point(d.bbox), zone.polygon)
        ]
        key = f"{rule.camera_id}:{rule.id}"
        is_open = key in state.open_events

        if intruders and not is_open:
            if now >= state.cooldown_until.get(key, 0.0):
                state.open_events[key] = now
                present_classes = sorted({d.class_name for d in intruders})
                return [
                    self._event(
                        rule, key, "intrusion_detected", "open", now,
                        {"object_count": len(intruders), "classes": present_classes},
                    )
                ]
        elif not intruders and is_open:
            started = state.open_events.pop(key)
            state.cooldown_until[key] = now + rule.cooldown_seconds
            return [
                self._event(
                    rule, key, "intrusion_ended", "resolved", now,
                    {"duration_seconds": int(now - started)},
                )
            ]
        return []

    # ----- line crossing (per track, directional) -------------------------

    def _eval_line_crossing(self, state, rule: Rule, detections, now) -> list[BusinessEvent]:
        """Emit a directional crossing event when a tracked object's foot point
        flips from one side of the configured line to the other.

        config: ``{"line": [[x1,y1],[x2,y2]], "direction": "in"|"out"|"both"}``.
        A cross from the right side (-1) to the left (+1) is "in"; the reverse is
        "out". Requires track ids (raise the camera's sample FPS for reliability)."""
        line = rule.config.get("line")
        if not isinstance(line, list) or len(line) != 2:
            return []
        a, b = (float(line[0][0]), float(line[0][1])), (float(line[1][0]), float(line[1][1]))
        classes = self._rule_classes(rule, ("person",))
        wanted = rule.config.get("direction", "both")
        events: list[BusinessEvent] = []
        seen: set[int] = set()

        for det in detections:
            if det.class_name not in classes or det.track_id is None:
                continue
            side = side_of_line(foot_point(det.bbox), a, b)
            if side == 0:
                continue
            seen.add(det.track_id)
            skey = (rule.id, det.track_id)
            prev = state.line_side.get(skey)
            state.line_side[skey] = side
            if prev is None or prev == side:
                continue
            direction = "in" if side > 0 else "out"
            ckey = f"{rule.camera_id}:{rule.id}:{det.track_id}"
            if wanted not in ("both", direction) or now < state.cooldown_until.get(ckey, 0.0):
                continue
            state.cooldown_until[ckey] = now + rule.cooldown_seconds
            # Unique key per crossing — each crossing is its own (momentary) alert.
            event_key = f"{ckey}:{int(now * 1000)}"
            events.append(
                self._event(
                    rule, event_key, "line_crossed", "open", now,
                    {"track_id": det.track_id, "direction": direction, "object_class": det.class_name},
                )
            )

        # Drop side-state for tracks no longer visible (bounded memory).
        for skey in list(state.line_side):
            if skey[0] == rule.id and skey[1] not in seen:
                del state.line_side[skey]
        return events

    # ----- count-based (queue / occupancy) --------------------------------

    def _eval_count(
        self, state, rule: Rule, zone: Zone, persons, now, open_type, resolve_type
    ) -> list[BusinessEvent]:
        threshold = int(rule.config.get("threshold", 5))
        count = count_people_in_zone([p.bbox for p in persons], zone.polygon)
        key = f"{rule.camera_id}:{rule.id}"
        is_open = key in state.open_events

        if count > threshold and not is_open:
            if now >= state.cooldown_until.get(key, 0.0):
                state.open_events[key] = now
                return [
                    self._event(rule, key, open_type, "open", now, {"count": count, "threshold": threshold})
                ]
        elif count <= threshold and is_open:
            started = state.open_events.pop(key)
            state.cooldown_until[key] = now + rule.cooldown_seconds
            return [
                self._event(
                    rule, key, resolve_type, "resolved", now,
                    {"count": count, "duration_seconds": int(now - started)},
                )
            ]
        return []

    # ----- loitering (per track) ------------------------------------------

    def _eval_loitering(self, state, rule: Rule, zone: Zone, persons, now) -> list[BusinessEvent]:
        threshold = int(rule.config.get("threshold_seconds", 60))
        events: list[BusinessEvent] = []
        in_zone: set[int] = set()

        for p in persons:
            if p.track_id is None or not point_in_polygon(foot_point(p.bbox), zone.polygon):
                continue
            in_zone.add(p.track_id)
            tkey = (rule.id, p.track_id)
            entered = state.loiter_entered.setdefault(tkey, now)
            key = f"{rule.camera_id}:{rule.id}:{p.track_id}"
            if (
                now - entered >= threshold
                and key not in state.open_events
                and now >= state.cooldown_until.get(key, 0.0)
            ):
                state.open_events[key] = now
                events.append(
                    self._event(
                        rule, key, "loitering_detected", "open", now,
                        {"track_id": p.track_id, "dwell_seconds": int(now - entered)},
                    )
                )

        # Resolve tracks that left the zone.
        for tkey in list(state.loiter_entered):
            rid, tid = tkey
            if rid != rule.id or tid in in_zone:
                continue
            del state.loiter_entered[tkey]
            key = f"{rule.camera_id}:{rule.id}:{tid}"
            if key in state.open_events:
                started = state.open_events.pop(key)
                state.cooldown_until[key] = now + rule.cooldown_seconds
                events.append(
                    self._event(
                        rule, key, "loitering_ended", "resolved", now,
                        {"track_id": tid, "duration_seconds": int(now - started)},
                    )
                )
        return events

    # ----- unattended billing counter (absence) ---------------------------

    def _eval_unattended(self, state, rule: Rule, zone: Zone, persons, now) -> list[BusinessEvent]:
        threshold = int(rule.config.get("threshold_seconds", 60))
        present = any(point_in_polygon(foot_point(p.bbox), zone.polygon) for p in persons)
        key = f"{rule.camera_id}:{rule.id}"

        if present:
            state.absence_since.pop(rule.id, None)
            if key in state.open_events:
                started = state.open_events.pop(key)
                state.cooldown_until[key] = now + rule.cooldown_seconds
                return [
                    self._event(
                        rule, key, "billing_counter_staffed", "resolved", now,
                        {"duration_seconds": int(now - started)},
                    )
                ]
            return []

        since = state.absence_since.setdefault(rule.id, now)
        if (
            now - since >= threshold
            and key not in state.open_events
            and now >= state.cooldown_until.get(key, 0.0)
        ):
            state.open_events[key] = now
            return [
                self._event(
                    rule, key, "unattended_billing_counter", "open", now,
                    {"empty_seconds": int(now - since)},
                )
            ]
        return []

    @staticmethod
    def _event(rule: Rule, key: str, event_type: str, status: str, now: float, metadata) -> BusinessEvent:
        return BusinessEvent(
            event_key=key,
            camera_id=rule.camera_id,
            organization_id=rule.organization_id,
            store_id=rule.store_id,
            rule_id=rule.id,
            event_type=event_type,
            status=status,
            severity=rule.severity,
            occurred_at=now,
            metadata=metadata,
        )
