# Contributing

## Development Setup

```bash
git clone https://github.com/yourname/pulpitink.git
cd pulpitink
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pulpitink doctor
```

## Commit Style

Use conventional commits:

```text
feat: add audio preprocessing presets
fix: handle missing ffmpeg
docs: update license policy
test: add srt exporter tests
```
