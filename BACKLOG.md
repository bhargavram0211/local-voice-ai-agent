# Backlog

Items deferred for later. Not in current scope.

---

## Environment / Tooling

- **uv sync failing (av / FFmpeg build)**  
  `uv sync` fails because the `av` package (PyAV, dependency of fastrtc → aiortc) builds from source and cannot find FFmpeg libraries (libavformat, libavcodec, etc.) via pkg-config. Fix options: install FFmpeg 7 and set `PKG_CONFIG_PATH`, or use pre-built wheels when available. Until then: use existing venv and `python -m pytest tests/ -v` for Phase 1 tests; run voice app with existing working environment.

---

*Add new backlog items below.*
