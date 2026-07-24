# affine_add_app — teaching coding application

Small, binary-free teaching app used by the **coding** language game examples.

## Layout

```
affine_add_app/
  README.md
  main.py          # Python entry (run locally)
  addlib.c         # C twin for LLVM narrative demos
  app_manifest.json
```

## Run locally (no Affine binary)

```bash
python3 main.py
# → AffineAddApp: 2 + 2 = 4
```

## Membrane path

1. `POST /language-invariant/game/coding/ingest` with `workspace_hint=fixtures/coding/affine_add_app`
2. `POST /language-invariant/game/coding/project` — CodingContextAgent projects compile/MCP narrative
3. Optional: UMC `domain=coding` Long Play (`examples/08_…`, `13_…`)

This app is **text only** — never commit compiled objects.
