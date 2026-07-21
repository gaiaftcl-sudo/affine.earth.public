# Create an Affine.Earth Account (Signup)

**Observed live on 2026-07-20** against [`https://affine.earth`](https://affine.earth) → [`/language-game/`](https://affine.earth/language-game/).

This is **step 1** before harness runs that need a live Affine session. Affine.Earth does **not** use email/password signup. Entry is **wallet-based** (“Sovereign entry”).

> **Media policy:** The signup / login walkthrough video (`affine-earth-demo-signup-app-qa.*` / `demo-signup-app-qa.gif`) appears **only on this page**. Everywhere else links here. For Games all-tests proof, see [Home](Home) and [In action](In-Action).

---

## Correct flow (do this — not the old healthz-only clip)

1. Open Sovereign entry / **New wallet**
2. Check the **content / consent** checkbox (`#loginConsent`)
3. Click **Use my location** (`#loginGeoBtn`) so latitude / longitude microdegrees fill
4. Click **Create wallet + QFOT** (`#loginCreateBtn`)
5. Wait until the **app opens** (login gate closes; Franklin chat + Docs drawer appear)

**Measured:** app opened ~8 seconds after Create on a fresh browser profile. Profile button then shows a truncated `bc1…` receive address.

---

## What “account” means here

| Classical expectation | What the live UI actually does |
|:---|:---|
| Email + password register | **Not present** |
| Username / OAuth | **Not present** |
| Create account | **New wallet** → consent → **Use my location** → **Create wallet + QFOT** → app opens |
| Session / credentials | Browser **IndexedDB** edge wallet + profile (`gaiaftcl-sovereign`); **Export private key** (hex) from Docs / Profile |
| API key minted at signup | **Not observed** in the signup UI |

UI lead text: *“No username. No password. Keys stay in this browser.”*

---

## Demo (CORRECT — supersedes healthz-only clip)

> **Supersedes** `affine-earth-demo-signup-healthz.*` / `demo-signup-healthz.gif` (those stopped at sterile healthz JSON and missed consent → location → create → app → Q&A).

<p>
<video controls width="720" poster="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-05-app-opened.png">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-app-qa.mp4" type="video/mp4">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-app-qa.webm" type="video/webm">
</video>
</p>

![Animated walkthrough — consent → location → Create wallet → app → Games / Q&A](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-signup-app-qa.gif)

> **MP4 / WebM:** [affine-earth-demo-signup-app-qa.mp4](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-app-qa.mp4) · mirrored at [`docs/media/`](https://github.com/gaiaftcl-sudo/affine.earth.public/tree/main/docs/media).

---

## Step-by-step screenshots (live UI)

### 1. Land on language-game / Sovereign entry

![Landing — Sovereign entry](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-01-landing.png)

1. Browse to `https://affine.earth`.
2. Final URL: `https://affine.earth/language-game/`.
3. If no prior browser profile exists, **Sovereign entry** (`#loginGate`) overlays the Franklin chat UI.

### 2. New wallet tab

![New wallet tab](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-02-new-wallet.png)

Select **New wallet** (`#tabNewUser`). Read **SOVEREIGN NODE INITIALIZATION** in the onboard docs panel.

### 3. Consent checkbox

![Consent checked](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-03-consent.png)

Check `#loginConsent`. Locale projection may shorten the label to: *“Consent required to create an edge wallet + genesis QFOT credit.”*  
Static HTML consent string includes: create a new Bitcoin mainnet wallet in this browser (zero BTC on-chain), genesis QFOT `100/1`, and export private key now.

### 4. Use my location

![Use my location filled](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-04-use-my-location.png)

Click **Use my location (optional)** (`#loginGeoBtn`). Measured: lat/lon fields fill with **microdegrees** (example NYC grant → `40712800` / `-74006000`). Status: *“Location anchored as microdegrees (optional) · ±0 m.”*

Footer still says create works if geolocation is denied — but the **correct documented path enables location**.

### 5. Create wallet + QFOT → app opens

![App opened after Create](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-05-app-opened.png)

Click **Create wallet + QFOT**. Status shows *“Creating edge mainnet wallet + genesis QFOT…”* then the gate closes.

**Observed after open:**

- Chat: *“SOVEREIGN NODE INITIALIZATION complete. Genesis QFOT `100/1` credited. **Export your private key now** …”*
- Docs drawer opens with the same export critical action
- Top bar **Profile** control becomes a truncated `bc1…` address

### 6. Export private key (manual)

![Profile — export surface](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-08-profile-export.png)

Use **Export private key** (`#exportKeyBtn`) or Docs export. Store offline. **Never commit private keys, wallet hex, or IndexedDB dumps to git.**

---

## Where test Q&A appear in the UI (not only CLI)

After the app opens:

### Path A — Language games catalog

![Games catalog](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-06-games-catalog-qa.png)

1. Click **Games** (`#gamesBtn`)
2. Side drawer **Language games** loads `GET /language-invariant/games` (measured: **12 LIVE** games)
3. Select **Linguistic membrane (chat)** for the primary human Q&A surface  
   Other LIVE surfaces: Formal manifold, Coding — UMC + MCP, Cinema, Aviation, Wallet · QFOT, Torsion dialogue, …

### Path B — Chat question / answer / verification

![Q&A answer + clarifying verify fields](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-07-qa-answer-verify.png)

| UI control | Role |
|:---|:---|
| `#messageList` assistant bubbles | Question / prompt display |
| User bubbles + Franklin replies | Answer turns |
| “Your clarifying answer…” / “Anything else?” | Verification / clarification UI |
| “Visual geometry” / “Agentic decomposition” chips | Prompt entry points under the init message |
| “Message Franklin…” composer | Free-form human-verifiable Q&A |
| Games → Formal manifold / Coding | Domain test surfaces |

CLI test banks remain in [Human-Verifiable Test Bank](Human-Verifiable-Test-Bank-and-Answers) and `llm_llvm_bench` suites — they are **in addition to**, not instead of, this UI path.

---

## Returning user (existing BTC address)

1. **Returning** tab (`#tabReturning`)
2. Enter a **BTC receive address** you control (`#loginAddress`)
3. Optionally **Use my location**
4. **Sign in** (`#loginSubmit`)

---

## Optional domain / aviation roles (New wallet)

| Value | Label (live HTML) |
|:---|:---|
| *(empty)* | General (default) · genesis 100/1 — no domain required |
| `aviation_traveler` | Traveler — genesis 50/1 |
| `aviation_pilot` | Pilot — genesis 1000/1 |
| `aviation_atc` | ATC — genesis 50000/1 |
| `aviation_land_crew` | Land Crew — genesis 200/1 |
| `aviation_terrestrial_weather` | Terrestrial Weather — genesis 500/1 |
| `aviation_solar_space_weather` | Solar / Space Weather — genesis 500/1 |

---

## Client wiring (from live JS)

`wallet-login.js` → `onboardNewUser`:

1. Require consent
2. `EdgeBTCWallet.createMainnetWallet()` (local IndexedDB)
3. `POST /language-invariant/economics-onboard` with `{ address, lat_microdegrees, lon_microdegrees, location_source, consent_create_wallet, … }`
4. `signIn` / bind profile; UI calls `showLoginGate(false)` and instructs **Export your private key now**

---

## Automated smoke (no fake users)

```bash
python3 scripts/check_affine_signup_surface.py
# or
AFFINE_LIVE_SMOKE=1 python3 -m pytest tests/test_affine_signup_surface.py -v
```

Asserts consent checkbox, **Use my location** control, Create wallet + QFOT, Games / messageList markers. Does **not** create wallets.

### Manual-only

| Step | Why manual |
|:---|:---|
| Consent + location + Create wallet | Creates a real browser mainnet edge wallet / identity |
| Private key export & backup | Security-sensitive |
| Returning Sign in with a live address | Requires an address the operator controls |
| Proven genesis QFOT ledger credit | **Live** after `POST …/economics-onboard` (see FoT table) |

---

## FoT measured 2026-07-20 (updated evening) — FIXED

**Status: FIXED** (GaiaFTCL SHA `cf3cd8249`, deployed to 9 cells). Earlier the same day the Python language-inject sidecar returned **HTTP 404** on `POST …/economics-onboard`, so Create wallet opened the app while Profile could show **BLOCKED / 0/1**. That route is restored; do not treat the old 404 / BLOCKED UI reading as current.

| Observation | Result |
|:---|:---|
| Correct UI path (consent → location → Create) | **App opens** (~2–8s); Franklin chat + Docs + `bc1…` profile |
| Profile after create (UI E2E re-verify) | **BALANCE STATUS: PROVEN** · **QFOT BALANCE: 100/1** · **GENESIS QFOT: 100/1** (not BLOCKED / 0/1) — [screenshot](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-flow-07-profile-qfot-proven.png) |
| `POST https://affine.earth/language-invariant/economics-onboard` | **HTTP 200** · `PROVEN_ECONOMICS_ONBOARD` · `genesis_credited: 100/1` (fix SHA `cf3cd8249`; route was missing on Python language-inject sidecar; Swift serve already had the handler) |
| Empty-body / no-consent probe | **HTTP 200** · `REFUSED` / `BLOCKED_ONBOARD_CONSENT` (not 404) |
| `GET …/qfot-balance?address=…` after onboard | **PROVEN** · `qfot_balance_canonical: 100/1` |
| Games → Linguistic membrane | `#messageList` reachable (LIVE catalog) |
| Email / password / captcha | **Absent** |
| `GET /language-invariant/games` | **HTTP 200** · 12 LIVE games |
| `GET /language-invariant/healthz` | **HTTP 200** · includes `economics_onboard: true` |
| `GET /v1/models` with Bearer probe | **HTTP 200** but **`text/html`** (SPA), not OpenAI models JSON |

**Historical note:** Pre-fix FoT same day recorded `economics-onboard` **HTTP 404** → genesis credit absent → Profile **BLOCKED / 0/1**. Post-fix + UI re-verify: **PROVEN / 100/1**.

**Implication:** Third parties **can** complete Sovereign entry, receive genesis QFOT on the language.sqlite hash index, and use in-app Games / Linguistic membrane Q&A. Do **not** claim public OpenAI-compatible `/v1` scoring until `/v1` returns JSON.

---

## Related

- [Getting Started](Getting-Started) — UI path first, then CLI
- [Capabilities](Capabilities) — Games / Q&A surfaces
- [Human-Verifiable Test Bank](Human-Verifiable-Test-Bank-and-Answers) — UI + package prompts
- [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction)
- [FAQ](FAQ)
