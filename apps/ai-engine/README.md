# @visionops/ai-engine

VisionOps AI computer-vision inference service.

## Responsibility
Consumes sampled frames from the pipeline bus, runs detection (YOLOv11) +
tracking (ByteTrack) + conditional enrichment, and emits structured detections
to TimescaleDB / the rule bus. **GPU-bound; scales independently** of the API.

## Structure
```
src/
├── main.py        # service lifecycle (Phase 2)
├── config.py      # settings
├── detectors/     # YOLOv11, fire/smoke, PPE ...   (Phase 7)
├── tracking/      # ByteTrack                        (Phase 7)
├── enrichment/    # LPR, OCR, pose, VLM router       (Phase 7)
├── pipeline/      # frame consumer → emitter         (Phase 7)
└── models/        # model loading (ONNX/TRT/Triton)  (Phase 7)
```

## Develop
```bash
pip install -e ".[dev]"        # light skeleton deps
pip install -e ".[dev,ml]"     # + heavy ML deps (needs system libs / GPU)
python -m src.main             # run service
pytest -q
```
ML dependencies are isolated under the `ml` extra so CI/skeleton stays fast.
