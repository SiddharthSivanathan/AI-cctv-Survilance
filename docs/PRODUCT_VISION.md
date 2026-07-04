# VisionOps AI — Product Vision

## One-liner
Turn any business's existing CCTV into an always-on AI operations analyst that watches, understands, and acts — without new hardware.

## The problem
Every physical business already has cameras. Almost none of that footage is *used* — it's recorded, overwritten, and only reviewed after something goes wrong. Managers are blind to what's happening on the floor in real time: empty billing counters, long queues, empty shelves, safety violations, theft, idle staff, crowding. Human monitoring doesn't scale and is reactive.

## The vision
A multi-tenant SaaS platform that connects to existing RTSP/ONVIF cameras and runs continuous computer-vision + vision-language reasoning to:
- **See** — detect people, vehicles, products, PPE, fire/smoke, poses, and events.
- **Understand** — track objects over time and interpret operational scenes ("counter unmanned", "queue building", "shelf empty").
- **Act** — evaluate business rules, raise real-time alerts, and notify the right person on the right channel.
- **Explain** — generate daily/weekly/monthly AI reports with root-cause analysis and recommendations.

## Who it's for
Retail, supermarkets, warehouses, factories, hospitals, offices, hotels, restaurants, schools, manufacturing. Buyer = Ops/Store/Safety leaders. User = managers, analysts, security.

## Why now
Cheap open CV models (YOLOv11), practical self-hostable VLMs (Qwen2.5-VL), and cheaper GPU inference make "understand every camera continuously" economically viable for the first time.

## What makes it defensible
1. **No new hardware** — works with cameras businesses already own (fast adoption).
2. **No-code rule engine** — operations teams encode their own domain logic without engineers.
3. **VLM scene reasoning + RCA** — not just boxes, but *why* and *what to do*, in plain language.
4. **Vertical-tuned models** — a warehouse pipeline ≠ a supermarket pipeline.
5. **Privacy-first architecture** — events not video; consent-gated biometrics — sellable into regulated industries.

## Non-goals (v1)
- Selling cameras/hardware.
- Storing/streaming raw video as the primary product (we store events + short clips).
- Forensic/legal evidence certification.
- Consumer/home security.

## North-star metric
**Actioned alerts per camera per week** — proof the platform surfaces things operators actually act on (not noise).

## Success looks like
A store manager opens VisionOps in the morning and reads a one-paragraph AI summary of yesterday's operations, sees three alerts that mattered, and one recommendation that saves money — all from cameras they already had.
