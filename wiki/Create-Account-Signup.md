# Create an Affine.Earth Account (Signup)

**Observed live on 2026-07-20** against [`https://affine.earth`](https://affine.earth) (redirects to [`/language-game/`](https://affine.earth/language-game/)).

This is **step 1** for third parties before harness runs that need a live Affine session. Affine.Earth does **not** use email/password signup. Entry is **wallet-based** (“Sovereign entry”).

---

## What “account” means here

| Classical expectation | What the live UI actually does |
|:---|:---|
| Email + password register | **Not present** |
| Username / OAuth | **Not present** |
| Create account | **New wallet** tab → consent → **Create wallet + QFOT** |
| Session / credentials | Browser **IndexedDB** edge wallet + profile (`gaiaftcl-sovereign`); optional **Export private key** (hex) |
| API key minted at signup | **Not observed** in the signup UI |

UI lead text (static HTML): *“No username. No password. Keys stay in this browser.”*

---

## Screenshots (live UI)

![Hero — language-game with Sovereign entry](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/hero-language-game.png)

### Signup walkthrough (Returning ↔ New wallet ↔ healthz)

<p>
<video controls width="720" poster="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/hero-language-game.png">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-healthz.mp4" type="video/mp4">
  <source src="https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-healthz.webm" type="video/webm">
</video>
</p>

![Animated walkthrough — Sovereign entry tabs then live healthz JSON](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/demo-signup-healthz.gif)

> **MP4 / WebM:** [https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-healthz.mp4](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/affine-earth-demo-signup-healthz.mp4) · also mirrored at [`docs/media/`](https://github.com/gaiaftcl-sudo/affine.earth.public/tree/main/docs/media) in the public repo.


![Root redirects to language-game with Sovereign entry (Returning tab)](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-02-returning-tab.png)

![New wallet tab — sovereign node initialization + consent](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-03-new-wallet-tab.png)

![New wallet — optional domain expanded](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-04-new-wallet-optional-domain.png)

![New wallet — consent checkbox and Create wallet + QFOT actions](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/signup-05-new-wallet-consent-actions.png)

![New wallet (retake)](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/sovereign-entry-new-wallet.png)

![Optional domain (retake)](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/sovereign-entry-optional-domain.png)

![Live healthz JSON](https://raw.githubusercontent.com/wiki/gaiaftcl-sudo/affine.earth.public/assets/healthz-json-live.png)

Same files also live in the main repo at `wiki/assets/signup-*.png` (mirror:
`https://raw.githubusercontent.com/gaiaftcl-sudo/affine.earth.public/main/wiki/assets/…`
after that tree is pushed).

---

## Exact path observed (do not invent steps)

### A. Open the site

1. Browse to `https://affine.earth`.
2. The site lands on `https://affine.earth/language-game/` (measured redirect/final URL).
3. If no prior browser profile exists, the **Sovereign entry** dialog (`#loginGate`) is shown over the Franklin chat UI.

### B. Returning user (existing BTC address)

1. Leave or select the **Returning** tab (`#tabReturning`).
2. Enter a **BTC receive address** (`#loginAddress`, placeholder `bc1… or 1… / 3…`).
3. Optionally fill **Latitude** / **Longitude**, or click **Use my location (optional)**.
4. Click **Sign in** (`#loginSubmit`).

This path was **not** completed with a real address in this documentation pass (avoids junk identities). Form fields above are from the live DOM.

### C. New user (create wallet) — signup path

1. Select the **New wallet** tab (`#tabNewUser`).
2. Read **SOVEREIGN NODE INITIALIZATION** copy in the onboard docs panel (browser-local wallet; keys stay on device).
3. Check the consent checkbox (`#loginConsent`).  
   - Static HTML consent string includes: create a new Bitcoin mainnet wallet in this browser (zero BTC on-chain), genesis QFOT `100/1`, and export private key now.  
   - Locale projection may shorten the visible label (observed: “Consent required to create an edge wallet + genesis QFOT credit.”).
4. Optionally open **Optional capabilities — domain / aviation (not required)** and pick a role:

   | Value | Label (live HTML) |
   |:---|:---|
   | *(empty)* | General (default) · genesis 100/1 — no domain required |
   | `aviation_traveler` | Traveler — genesis 50/1 |
   | `aviation_pilot` | Pilot — genesis 1000/1 |
   | `aviation_atc` | ATC — genesis 50000/1 |
   | `aviation_land_crew` | Land Crew — genesis 200/1 |
   | `aviation_terrestrial_weather` | Terrestrial Weather — genesis 500/1 |
   | `aviation_solar_space_weather` | Solar / Space Weather — genesis 500/1 |

5. Latitude / longitude remain optional (footer: create works if geolocation is denied; BTC starts at zero sats).
6. Click **Create wallet + QFOT** (`#loginCreateBtn`).

**This documentation pass stopped before clicking Create** to avoid creating junk mainnet edge wallets. Client JS (`wallet-login.js` → `onboardNewUser`) is wired to:

1. Require consent.
2. Call `EdgeBTCWallet.createMainnetWallet()` (local IndexedDB).
3. `POST /language-invariant/economics-onboard` with `{ address, lat_microdegrees, lon_microdegrees, location_source, consent_create_wallet, … }`.
4. Bind / save profile; UI then instructs **Export your private key now**.

### D. After create (from live UI source — not exercised end-to-end here)

Profile drawer controls include:

- **Export private key** (`#exportKeyBtn`) — exports private key hex for offline backup.
- **Sign out (this browser)** — clears local profile gate.

---

## Gate for third-party harness testing

Before claiming a live Affine.Earth harness run:

1. **Create or restore a Sovereign entry session** (this page).
2. **Export / secure the private key** if you created a new wallet (manual; not automatable as a success claim).
3. **Confirm the model endpoint you will call** actually speaks OpenAI-compatible JSON (see blockers below).
4. Set `OPENAI_BASE_URL` / `OPENAI_API_KEY` (or harness env) only for an endpoint that returns real `/v1` JSON — then follow [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction).

Signup alone does **not** mint a classical `sk-…` API key in the UI observed on 2026-07-20.

---

## Automated smoke (no fake users)

Reachability of the signup surface (HTTP + HTML markers only):

```bash
# From llm-llvm-benchmark-suite/
python3 scripts/check_affine_signup_surface.py
# or
AFFINE_LIVE_SMOKE=1 python3 -m pytest tests/test_affine_signup_surface.py -v
```

These checks **do not** create wallets, sign in, or assert auth success.

### Manual-only (cannot automate as success)

| Step | Why manual |
|:---|:---|
| Consent + Create wallet | Creates a real browser mainnet edge wallet / identity |
| Private key export & backup | Security-sensitive; user must store offline |
| Returning Sign in with a live address | Requires a real address the operator controls |
| Email verification / captcha | **Not observed** on this surface |
| Genesis QFOT server credit | Depends on `POST …/economics-onboard` (see blockers) |

---

## Blockers measured 2026-07-20 (FoT)

| Observation | Result |
|:---|:---|
| Email / password / invite code fields | **Absent** on Sovereign entry |
| Captcha | **Not observed** |
| `POST https://affine.earth/language-invariant/economics-onboard` (empty JSON body probe) | **HTTP 404** `Not Found` |
| `GET https://affine.earth/v1/models` with `Accept: application/json` + `Authorization: Bearer uum8d-public-verifier` | **HTTP 200** but **`text/html`** (Franklin SPA), not OpenAI models JSON |
| `http://affine.earth/v1/models` | **Connection failed** on port 80 from this probe host |
| Health | `GET /language-invariant/healthz` → **HTTP 200** JSON `ok: true` |

**Implication:** Third parties can document and exercise the **signup UI path**, but must not assume that creating a wallet currently yields a working public OpenAI-compatible `/v1` for EleutherAI / BigCode / FastChat until `/v1` returns JSON and onboard endpoints accept POSTs. Use a verified compatible endpoint (or local interceptor only for **wiring**, not scoring — see FAQ).

---

## Related

- [Getting Started](Getting-Started) — account step is first for outsiders
- [Third-Party Harness Reproduction](Third-Party-Harness-Reproduction)
- [Capabilities](Capabilities)
- [FAQ](FAQ)
