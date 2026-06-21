# AI-SlowMatch PySide6 Desktop MVP

Run from the repository root:

```bash
python run_desktop.py
```

Install desktop dependencies first:

```bash
pip install -e ".[desktop]"
```

This GUI is a local-first MVP. It analyzes only text the user chooses to provide, uses a local heuristic/mock engine, and does not make remote provider calls.
