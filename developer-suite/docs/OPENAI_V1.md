# OpenAI-compatible `/v1` wire → Affine.Earth OS

**This is not cloud OpenAI.**  
`https://affine.earth/v1` uses an OpenAI-*compatible wire shape* so standard HTTP clients work. The engine behind the membrane is **Affine.Earth OS** only.

Do **not** point examples at `api.openai.com`, Anthropic (`api.anthropic.com`), Gemini cloud, Groq, Together, or ChatGPT API. Those are category errors for this suite.

## Env (canonical)

```bash
export AFFINE_BASE_URL="https://affine.earth"
export AFFINE_API_KEY="uum8d-hle-verifier"
# Wire aliases for OpenAI-shaped client libraries (same membrane):
export OPENAI_BASE_URL="${AFFINE_BASE_URL}/v1"
export OPENAI_API_KEY="${AFFINE_API_KEY}"
```

## Live surfaces

| Method | Path |
|--------|------|
| GET | `/v1/models` (+ `/openai/v1/*`, `/language-invariant/v1/*`) |
| POST | `/v1/chat/completions` |
| POST | `/v1/responses` (`store: false`) |
| GET/POST | `/v1/api-keys` |
| DELETE | `/v1/api-keys/{id}` |

Bearer required for chat/responses/api-keys. Bootstrap: `uum8d-hle-verifier`.

## Models (from live `GET /v1/models` only)

Do not invent model ids. Measured Affine.Earth OS ids:

- `gaiaftcl-os`
- `affine-earth-os-mcp`
- `franklin-membrane`
- `franklin-membrane-exam`

## Exam profile

```http
Authorization: Bearer uum8d-hle-verifier
X-Affine-Exam: hle
```

```json
{"model":"franklin-membrane-exam","messages":[{"role":"user","content":"What is 2+2?"}]}
```

SDK: `examples/03_openai_models_and_chat.py`, `examples/05_exam_hle_smoke.py`.  
Full HLE/ARC harnesses: parent `scripts/*openai*exam*.py` — do not re-implement here.
