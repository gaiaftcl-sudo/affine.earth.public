# Language games — teaching suite (measured)

Real membrane path: **ingest → project → context** for all 12 LIVE games,
plus the local **AffineAddApp** coding application (binary-free).

- Apex: `https://affine.earth`
- Started: `2026-07-24T14:51:06.590040+00:00`
- Finished: `2026-07-24T14:51:12.086548+00:00`
- Overall: **PASS** (12/12 games; coding app exit=0)
- Machine receipt: [`receipts/LANGUAGE_GAMES_TEACHING_RUN.json`](receipts/LANGUAGE_GAMES_TEACHING_RUN.json)

## Coding application (local)

Path: `fixtures/coding/affine_add_app/`

```text
AffineAddApp: 2 + 2 = 4
status=CALORIE_TEACHING_ADD
```

Wire into coding game via `workspace_hint=fixtures/coding/affine_add_app`
(see `examples/08_umc_coding_llvm_narrative.py` and `examples/games/coding.py`).

## How to re-run

```bash
cd developer-suite
python3 examples/13_all_language_games_teaching.py
python3 examples/11_game_ingest_project_domains.py
python3 examples/games/run_all.py
```

## Per-game teaching results

### `cinema` — PASS

Ingest a NarrativeManifoldSeed (film + characters); project locale Concept_IDs onto the cinema Gyroid.

- Seed keys: `H_end, H_start, amplitudes, characters, film_id, locale, node_id, session_id, statement, structural_bound, tau_height, title`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "cinema", "calorie": "CALORIE_NARRATIVE_MANIFOLD"}`
- project fields: `{"game_id": "cinema"}`

Teaching script: `examples/games/cinema.py`

### `aviation` — PASS

Ingest an AviationRole + flight_id; project role/telemetry Concept_IDs for the aviation manifold.

- Seed keys: `amplitudes, flight_id, locale, node_id, role, session_id, tau_height, title`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "aviation", "calorie": "CALORIE_AVIATION_ROLE_MATRIX"}`
- project fields: `{"game_id": "aviation"}`

Teaching script: `examples/games/aviation.py`

### `aviation_atc` — PASS

Ingest ATC sector/callsign/clearance (not chat); project sector-flow Concept_IDs.

- Seed keys: `amplitudes, callsign, clearance_kind, locale, node_id, sector_id, session_id, tau_height, title`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "aviation_atc", "calorie": "CALORIE_ATC_SECTOR_FLOW"}`
- project fields: `{"game_id": "aviation_atc"}`

Teaching script: `examples/games/aviation_atc.py`

### `gaming` — PASS

Ingest rule/desync labels for a session; project Gyroid/Shatter for gaming UMC state.

- Seed keys: `amplitudes, layer_labels, locale, node_id, session_id, tau_height, title`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "gaming", "calorie": "CALORIE_GAMING_RULE_DESYNC"}`
- project fields: `{"game_id": "gaming"}`

Teaching script: `examples/games/gaming.py`

### `coding` — PASS

Ingest a coding workspace (affine_add_app); project MCP/compile narrative via CodingContextAgent.

- Seed keys: `amplitudes, locale, node_id, session_id, statement, tau_height, title, workspace_hint`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "coding", "calorie": "CALORIE_GAV_CODING_LONG_PLAY"}`
- project fields: `{"game_id": "coding"}`

Teaching script: `examples/games/coding.py`

### `reality` — PASS

Ingest RealityRoom presence OperatorTensor; project room.manifold Gyroid fuse.

- Seed keys: `amplitudes, locale, node_id, presence_id, room_id, session_id, title, torsion_den, torsion_num`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "reality", "calorie": "CALORIE_REALITY_IMMERSION"}`
- project fields: `{"game_id": "reality"}`

Teaching script: `examples/games/reality.py`

### `topological_sandbox` — PASS

Ingest heal|shatter OperatorTensor; project Mirror Manifold WebGL primitives.

- Seed keys: `action, amplitudes, locale, node_id, session_id, title, torsion_den, torsion_num`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "topological_sandbox", "calorie": "CALORIE_TOPOLOGICAL_SANDBOX"}`
- project fields: `{"game_id": "topological_sandbox"}`

Teaching script: `examples/games/topological_sandbox.py`

### `formal_manifold` — PASS

Ingest LogicalAmplitudeTensor (statement + amplitudes); project COLLAPSE/DIVERGENCE.

- Seed keys: `amplitudes, domain, locale, node_id, session_id, statement, tau_height, title`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "formal_manifold", "calorie": "CALORIE_MANIFOLD_OBSERVER"}`
- project fields: `{"game_id": "formal_manifold"}`

Teaching script: `examples/games/formal_manifold.py`

### `wallet_qfot` — PASS

Ingest wallet bind / zero QFOT transfer (Rational); project profile + economics subjects.

- Seed keys: `address, amount_den, amount_num, amplitudes, domain, lat_micro, locale, lon_micro, node_id, session_id, title`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "wallet_qfot", "calorie": "CALORIE_WALLET_QFOT"}`
- project fields: `{"game_id": "wallet_qfot"}`

Teaching script: `examples/games/wallet_qfot.py`

### `linguistic_membrane` — PASS

Ingest intent+SCF+signature envelope; project sovereign linguistic kinds (no elephant text).

- Seed keys: `amplitudes, intent, locale, node_id, scf_hash, session_id, title, user_vqbit_hash, vqbit_signature`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "linguistic_membrane", "calorie": "CALORIE_LINGUISTIC_MEMBRANE"}`
- project fields: `{"game_id": "linguistic_membrane"}`

Teaching script: `examples/games/linguistic_membrane.py`

### `umc_gav` — PASS

Ingest UMC Director ManifoldSeed; project Long Play viewport subjects.

- Seed keys: `amplitudes, domain, locale, max_turns, node_id, session_id, tau_height, title`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "umc_gav", "calorie": "CALORIE_UNIVERSAL_MANIFOLD_CONTROLLER"}`
- project fields: `{"game_id": "umc_gav"}`

Teaching script: `examples/games/umc_gav.py`

### `torsion_dialogue` — PASS

Ingest collaborative agreement OperatorTensor; project τ→0 fuse / local Shatter.

- Seed keys: `agreement, amplitudes, locale, node_id, operator_tensor, room_id, session_id, title`
- HTTP: ingest 200 · project 200 · context 200
- ingest fields: `{"status": "CALORIE_GAME_INGEST", "game_id": "torsion_dialogue", "calorie": "CALORIE_TORSION_DIALOGUE"}`
- project fields: `{"game_id": "torsion_dialogue"}`

Teaching script: `examples/games/torsion_dialogue.py`

## Architecture (developer view)

```text
teaching seed (game_seeds.py)
        │
        ▼
POST /language-invariant/game/{id}/ingest   ← real ingestion
        │
        ▼
POST /language-invariant/game/{id}/project  ← real projection
        │
        ▼
GET  /language-invariant/game/{id}/context  ← observer context
```

No OS binaries. No mocks. Apex Affine.Earth OS membrane only.
