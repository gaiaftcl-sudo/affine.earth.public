# OpenAI-compatible `/v1`

Live on Affine.Earth OS (not api.openai.com):

| Method | Path |
|--------|------|
| GET | `/v1/models` (+ `/openai/v1/*`, `/language-invariant/v1/*`) |
| POST | `/v1/chat/completions` |
| POST | `/v1/responses` (`store: false`) |
| GET/POST | `/v1/api-keys` |
| DELETE | `/v1/api-keys/{id}` |

Bearer required for chat/responses/api-keys. Bootstrap: `uum8d-hle-verifier`.

Exam profile:

```http
Authorization: Bearer uum8d-hle-verifier
X-Affine-Exam: hle
```

```json
{"model":"franklin-membrane-exam","messages":[{"role":"user","content":"What is 2+2?"}]}
```

Full HLE/ARC harnesses: parent `scripts/*openai*exam*.py` — do not re-implement here.
