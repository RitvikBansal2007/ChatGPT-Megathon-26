# GreenDash edge proxy (Caddy)

`infra/Caddyfile` is the only public entry point for the dashboard. It forwards to the
Streamlit UI on `127.0.0.1:8501` and nothing else.

> **Status:** validated with Caddy v2.11.7 and smoke-tested locally over plain HTTP
> against the real Streamlit UI (Basic Auth gate, headers, API-path blocking,
> WebSocket, 502 handling). **HTTPS on a real hostname has NOT been verified** (no
> hostname exists yet, no certificate was issued). Do not describe a deployment as
> HTTPS-ready until the checklist at the bottom is done on the real host.
>
> **This proxy is a temporary perimeter gate, not application security.** Read
> "Temporary Basic Auth gate" below before exposing it to anyone. Do not put this
> UI on the open internet: the demo-token flow lets any visitor pick any role
> (including Evaluator and Auditor) inside the app, so there is still no per-user
> sign-in behind this gate.

## What it does

| Requirement | How |
|---|---|
| Frontend public, API not | One upstream only: `reverse_proxy 127.0.0.1:8501`. `/api`, `/docs`, `/redoc`, `/openapi.json` and `/healthz` return 404 from Caddy and are never forwarded. Port 8000 is not referenced as an upstream. |
| WebSockets | Streamlit's `/_stcore/stream` is a WebSocket; Caddy's `reverse_proxy` upgrades it automatically, no extra config. |
| `font-src 'self'` and `frame-ancestors 'none'` | In the `Content-Security-Policy` header below. |
| Errors carry the headers too | The header snippet is imported in `handle_errors` as well, so Caddy-generated 4xx/5xx (e.g. 502 when Streamlit is down) include them. |
| Domain not invented | Hostname comes from `GREENDASH_DOMAIN`; falls back to `localhost`. |

## Temporary Basic Auth gate

Everything behind the proxy (pages, static files, the Streamlit WebSocket handshake and
the blocked API paths) requires HTTP Basic Auth. It is **one shared username and
password** for trusted demo users. It is **not** per-user sign-in, not an audit trail
and not API authorization. It exists so the demo is not world-readable while real
authentication is built.

**Required environment variables** (nothing is stored in the repo):

| Variable | Meaning |
|---|---|
| `GREENDASH_BASIC_AUTH_USER` | The shared username. |
| `GREENDASH_BASIC_AUTH_HASH` | A **bcrypt hash** of the password, never the password. |

**Generate a hash** with the Caddy binary you already use. Run it without
`--plaintext` so the password is not left in your shell history:

```bash
caddy hash-password          # prompts twice, prints a $2a$14$... bcrypt hash
```

**Set both variables in the environment of the Caddy process.** Caddy does **not** read
the application's `.env` file (`Code/.env`, `.env.example`) or a `.env` next to the
Caddyfile; this was tested and such a file is ignored, so Caddy would refuse to start.
The hash is a secret: keep it out of git and out of `.env.example`.

1. **Env file passed to Caddy (recommended; tested).** Put it outside the repo, readable
   only by the user that runs Caddy (`chmod 600`):

   ```
   # /etc/greendash/caddy.env
   GREENDASH_BASIC_AUTH_USER=demo
   GREENDASH_BASIC_AUTH_HASH='$2a$14$...'
   ```

   ```bash
   caddy validate --config infra/Caddyfile --adapter caddyfile --envfile /etc/greendash/caddy.env
   caddy run      --config infra/Caddyfile --adapter caddyfile --envfile /etc/greendash/caddy.env
   ```

2. **Shell environment (tested).** Use **single quotes**; in double quotes the shell
   expands `$2a`, `$14` and corrupts the hash:

   ```bash
   export GREENDASH_BASIC_AUTH_USER=demo
   export GREENDASH_BASIC_AUTH_HASH='$2a$14$...'
   caddy run --config infra/Caddyfile --adapter caddyfile
   ```

   ```powershell
   $env:GREENDASH_BASIC_AUTH_USER = 'demo'
   $env:GREENDASH_BASIC_AUTH_HASH = '$2a$14$...'
   caddy run --config infra/Caddyfile --adapter caddyfile
   ```

3. **systemd service (standard feature, not tested here).** Run the same `--envfile`
   command in `ExecStart=`, with the file referenced above.

Rules for all three:

- `caddy validate` needs the same variables, otherwise it (correctly) fails.
- **Do not use `caddy run --environ`:** it prints the whole environment, including the
  hash, to the log.
- A wrong or corrupted hash does not fail loudly; every login simply returns `401`.
  After setting it, confirm a request with the real password succeeds.

**It fails closed.** Verified with `caddy validate` and `caddy run`:

| Situation | Result |
|---|---|
| Username and hash both set, valid | Starts; requests without the password get `401` |
| Either or both unset or empty | Caddy refuses to start (config error) |
| Hash is not a bcrypt/base64 value (for example a plaintext password) | Caddy refuses to start |
| Hash looks valid but is truncated or wrong | Caddy starts, and **every** request, including the correct password, gets `401` |

Not covered by the gate, by design:

- **No lockout or rate limiting.** bcrypt cost 14 slows guessing but does not stop it.
  Use a long random password.
- **Credentials are sent with every request.** Only use this over HTTPS on a real host.
  Over plain HTTP they are readable on the network.
- **One shared secret.** Anyone who has it can use every role in the app.
- **The credential is not forwarded** to Streamlit (`Authorization` is stripped) and is
  never written to the repo.

## Headers set on every response

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self';
  connect-src 'self' wss://$GREENDASH_DOMAIN; media-src 'self' data: blob:;
  worker-src 'self' blob:; frame-src 'self'; manifest-src 'self'; object-src 'none';
  base-uri 'self'; form-action 'self'; frame-ancestors 'none'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), microphone=(), payment=(), usb=()
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Resource-Policy: same-origin
(Server header removed)
```

`Strict-Transport-Security` is **not** set by default. A wrong HSTS value sticks in
browsers for its whole `max-age`. Uncomment the line in the Caddyfile only after HTTPS is
verified on the real hostname.

## What was verified (and how)

Caddy v2.11.7 (official release, checksum verified), Streamlit 1.65.0, fixtures mode,
Chromium-based browser, `127.0.0.1` only:

- `caddy validate --config Code/infra/Caddyfile --adapter caddyfile`: valid, also with
  `GREENDASH_DOMAIN` set; `caddy fmt --diff` clean. The adapted JSON has exactly one
  upstream, `127.0.0.1:8501`.
- Through Caddy (smoke copy of the Caddyfile that differs only in the site address, so
  it can listen on a test port without TLS): `/` returns 200 with every header above;
  `/api/...`, `/docs`, `/openapi.json`, `/healthz` return 404 with the headers; with
  Streamlit stopped, `/` returns 502 **with** the CSP and all other headers; nothing
  listens on port 8000.
- WebSocket: a handshake to `/_stcore/stream` returns `101 Switching Protocols`
  through Caddy, and the Customer Hub, Cockpit and Receipts pages render through
  Caddy (their content arrives over that WebSocket) with no CSP violations in the
  console.
- Basic Auth (throwaway test credential, plain HTTP, loopback): without credentials
  or with a wrong user or password, `/`, a page, `/_stcore/health`, a static font,
  `/api/...`, `/docs` and the WebSocket handshake all return `401` with
  `WWW-Authenticate` and the security headers; with valid credentials the pages load,
  the WebSocket returns `101`, and `/api/...`, `/docs`, `/openapi.json`, `/healthz`
  still return `404`; a POST to `/api/auth/demo-token` returns `401` without
  credentials and `404` with them. With Streamlit stopped, valid credentials get a
  `502` carrying the headers. The fail-closed table above was exercised with
  `caddy validate` and `caddy run`.

## CSP details

Observed while testing:

- Pages render and the WebSocket session works with `script-src` **without**
  `'unsafe-eval'` and `connect-src 'self'`.
- Only one violation was reported: Streamlit's own bundled **KaTeX math font**
  (`data:` URI) is blocked by `font-src 'self'`. The app does not render LaTeX, so
  nothing visible changes. If a future page uses `st.latex` or `$...$` math, the math
  glyphs will fall back to a default font. Fixing that means adding `data:` to
  `font-src`, which departs from the stated requirement; decide that deliberately.
- `style-src 'unsafe-inline'` and `script-src 'unsafe-inline'` are required: Streamlit
  and the brand UI inject inline styles and Streamlit bootstraps with an inline script.
  This is weaker than a nonce-based CSP; Streamlit does not support nonces.

Not covered:

- HTTPS on a real hostname (certificate issuance, `wss://` in production, HSTS).
- Scenario Lab, `st.components` iframes, file uploads, live-API mode.
- Safari and Firefox. Older Safari does not treat `'self'` as covering `wss://`, which is
  why `connect-src` also lists `wss://$GREENDASH_DOMAIN`.
- `frame-ancestors 'none'` blocks embedding in any iframe, including any internal portal
  that wants to embed the dashboard.

## Run it

Caddy is **not** installed by this repo. Install it from your platform's official
package source, then from `Code/`:

```bash
# 1. validate (syntax and directive check; does not start anything). This needs the
#    two GREENDASH_BASIC_AUTH_* variables too (step 3), or it fails by design.
caddy validate --config infra/Caddyfile --adapter caddyfile

# 2. start the app on loopback only (API on 8000 is only for the UI process)
make app         # binds uvicorn to 127.0.0.1:8000 and Streamlit to 127.0.0.1:8501

# 3. credentials are required even for local runs, in the CADDY process environment
#    (not the app's .env). Use single quotes. Or pass --envfile (see the gate section).
export GREENDASH_BASIC_AUTH_USER=demo
export GREENDASH_BASIC_AUTH_HASH='<output of: caddy hash-password>'

# 4. local test through Caddy (uses Caddy's internal CA, so the browser will warn)
caddy run --config infra/Caddyfile

# 5. production: set the real hostname
GREENDASH_DOMAIN=dashboard.example.org caddy run --config infra/Caddyfile
```

Check the result (expect `401` without credentials, then your headers and `404`
with them):

```bash
curl -sI https://<host>/ | head -1
curl -sI -u "$GREENDASH_BASIC_AUTH_USER" https://<host>/ | grep -i -E "content-security|x-frame"
curl -s -o /dev/null -w "%{http_code}\n" -u "$GREENDASH_BASIC_AUTH_USER" https://<host>/api/healthz
```

## Operational notes

- **Never bind Streamlit or the API to `0.0.0.0`.** Streamlit listens on all
  interfaces if `--server.address` is omitted (confirmed on 1.65.0). Keep
  `--server.address 127.0.0.1` in every run command.
- **Firewall:** expose only 80 and 443. Do not publish 8000 or 8501.
- **`GREENDASH_DOMAIN` must be a bare hostname.** A scheme or port (for example
  `https://host` or `host:8443`) produces an invalid `wss://` entry in the CSP.
- **Caddy stores data outside the repo** (on Windows `%APPDATA%\Caddy`, on Linux
  `~/.local/share/caddy`), including its local CA key when serving `localhost`. Do not
  commit or share it.
- **HTTPS for a real hostname** needs: a DNS record pointing at this host, ports 80 and
  443 reachable from the internet (for ACME), and `GREENDASH_DOMAIN` set. Caddy then
  obtains and renews certificates automatically. None of this has been verified for
  GreenDash.
- **Application authentication is not solved by this proxy.** See "What this does
  not secure" below.

## What this does not secure

The Basic Auth gate protects who can reach the UI. It does nothing about what a
person who is let in can do:

- **Roles are self-selected.** The UI's sidebar role switcher defaults to Evaluator
  and lets any visitor become Auditor, Relationship Manager and so on.
- **The demo-token endpoint is not authentication.** The API now validates signed
  bearer tokens and enforces roles and customer ownership, but in `ENV=demo`
  `POST /api/auth/demo-token` issues a token for any role to anyone who can call it
  (the UI uses it; the proxy blocks `/api/*` from outside, the Streamlit process
  reaches it over loopback). Real per-user sign-in does not exist yet.
- **`JWT_SECRET` is read from configuration and validated.** Any `ENV` other than
  `development`/`dev`/`test` requires a random secret of 32+ characters or the API
  refuses to start. Set it in the API process environment or its `.env` (this is
  separate from the Caddy process environment above).
- **No rate limiting, lockout or token revocation** on the API.

Public or live deployment must wait for per-user sign-in that replaces the demo-token
flow and the self-select role picker. Until then, treat the gate above as the only
perimeter protection and share the password only with trusted demo users.

## Before calling a deployment ready

- [ ] `caddy validate` passes with the real `GREENDASH_BASIC_AUTH_*` variables set.
- [ ] `GREENDASH_BASIC_AUTH_HASH` was generated with `caddy hash-password` and is not in git.
- [ ] Unauthenticated request returns `401` on `/`, a page and the WebSocket.
- [ ] Real per-user sign-in exists (the gate is temporary and `ENV=demo` hands out any
      role), or the audience is limited to trusted demo users.
- [ ] The API runs with a random `JWT_SECRET` (32+ characters) and, if feedback notes
      are used, a `DATA_KEY`.
- [ ] `GREENDASH_DOMAIN` set to the real hostname and DNS points at the host.
- [ ] Browser loads over HTTPS with no CSP violations in the console on every page.
- [ ] `/api/...` and `:8000` unreachable from outside.
- [ ] Headers above present on a normal page, a 404 and a 502.
- [ ] Then, and only then, enable HSTS.
