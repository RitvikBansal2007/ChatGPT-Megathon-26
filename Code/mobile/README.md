# GreenDash — Native Mobile App

> **Status: [DESIGN] — not built in the hackathon prototype.**
> The hackathon delivers a mobile-first responsive Streamlit Customer Hub tested at 390px.
> This document specifies the production Expo app that would follow from the same FastAPI contracts.

---

## Technology

| Concern | Choice |
|---|---|
| Framework | **Expo SDK 52** (React Native + TypeScript) |
| Navigation | Expo Router (file-based, tab + stack) |
| State | TanStack Query v5 (cache, background refresh) |
| Auth | OAuth2 + PKCE via `expo-auth-session` |
| Storage | `expo-secure-store` (Keychain / Keystore) — no PII in AsyncStorage |
| Biometrics | `expo-local-authentication` |
| Fonts | Inter Variable + Plus Jakarta Sans (already OFL, bundled) |
| Charts | Victory Native XL (SVG, accessible) |
| API | Same FastAPI contracts as the web app — zero duplication |

---

## Screen List

### 1. Login

| Item | Detail |
|---|---|
| **API endpoint** | `POST /api/auth/demo-token` (demo); OAuth2 PKCE flow in production |
| **Contract fields** | `access_token`, `token_type`, `expires_in`, `role` |
| **Design** | Mist background, greendash logo, "Sign in with your bank" button (Verdant, Abyss text, 56px) |
| **Auth** | Token stored in iOS Keychain / Android Keystore via `expo-secure-store`. Never in AsyncStorage. |
| **Biometrics** | On subsequent opens, `LocalAuthentication.authenticateAsync()` re-unlocks the stored token |
| **Security** | Screenshot blocked on this screen (`expo-screen-capture`) |

---

### 2. Hub (Pathways tab)

| Item | Detail |
|---|---|
| **API endpoint** | `GET /api/customers/{id}/opportunities` (Bearer JWT) |
| **Contract fields** | `status`, `likelihood_band`, `propensity`, `product`, `headline`, `why_now.display` |
| **Layout** | Vertical list of 4 pathway tiles, always visible; sorted RECOMMEND → SOFT_SURFACE; single column, 16px gutters |
| **Tile** | 390px wide, 80px tall, G2 glass card; status pill (icon + label, never colour alone); product name in H3 |
| **Tap** | Navigate to Proof Card screen for that pathway |
| **Empty state** | "No opportunities loaded" card with retry button |
| **Error state** | Friendly card — no stack trace; "Try again" button |

---

### 3. Proof Card (RECOMMEND)

| Item | Detail |
|---|---|
| **API endpoint** | `GET /api/customers/{id}/opportunities` — same response, single opportunity displayed |
| **Contract fields** | `headline`, `why_now`, `reason_codes[]`, `eligibility`, `impact`, `explanation`, `actions` |
| **Layout** | Scroll view, 16px padding, G2 glass card; 2px Verdant accent on card top |
| **Sections** | Status pill → Headline → Why-now chip → Evidence accordion → Three badges (separate) → Impact expander → Claim-Check stamp → Action buttons |
| **Impact** | `impact.family == "paper"` → show `paper.value` + `digital.value` only, never CO₂e |
| **Badges** | Three separate chips in a horizontal row: Likelihood (◎) · Eligibility (☑) · Impact quality (◔) |
| **Claim stamp** | "N of N sentences verified" strip; tap → bottom sheet listing each sentence + cited fields |
| **Primary CTA** | Full-width pill, 56px, Verdant fill, Abyss text |
| **Screenshot blocking** | `expo-screen-capture` — prevent on Proof Card (contains financial data) |
| **Accessibility** | All interactive elements ≥ 44pt tap target; VoiceOver / TalkBack tested |

---

### 4. ABSTAIN state

| Item | Detail |
|---|---|
| **Contract fields** | `status == "ABSTAIN"`, `impact.missing_inputs[0]` |
| **Layout** | Same card shell, amber pill "Need one thing" |
| **Content** | Names the single missing input; Confidence Ladder CTA: "Add [field]" → data-entry sheet |
| **Impact block** | Locked skeleton (no number shown) |

---

### 5. REVIEW state

| Item | Detail |
|---|---|
| **Contract fields** | `status == "REVIEW"`, `review.message`, `review.question`, `review.options` |
| **Layout** | Info-blue pill "Mixed signals"; impact hidden |
| **Content** | One yes/no confirming question as primary action |

---

### 6. RULED_OUT state

| Item | Detail |
|---|---|
| **Contract fields** | `status == "RULED_OUT"`, `eligibility.rules_fired[0]` |
| **Layout** | Slate Sage dimmed card, shield-check icon, no action button |
| **Content** | "Why not?" heading; plain-English rule text; "See what else fits" ghost link only |
| **Rule text** | Localised from `eligibility.rules_fired` — never raw rule ID shown to user |

---

### 7. SOFT_SURFACE state

| Item | Detail |
|---|---|
| **Contract fields** | `status == "SOFT_SURFACE"`, `headline` |
| **Layout** | Flat G1 glass, no top accent, "Good to know" pill |
| **Content** | Educational headline; "Learn more" link only |

---

### 8. Settings / Insights opt-out

| Item | Detail |
|---|---|
| **API endpoint** | `PUT /api/customers/{id}/insights-optout` (Bearer JWT) |
| **Contract fields** | `opted_out: bool`, `opted_out_at: datetime` |
| **Layout** | Standard settings list; "Green insights" toggle |
| **Behaviour** | Toggle off → confirmation sheet → PUT request → banner "You've turned off green insights" |
| **No PII cached** | Opt-out state stored server-side only; local cache cleared on sign-out |

---

## Auth flow (production)

```
App open
  └─ expo-secure-store: token present and not expired?
       ├─ Yes → LocalAuthentication.authenticateAsync() → unlock → proceed
       └─ No  → OAuth2 + PKCE (expo-auth-session)
                  → bank OAuth2 server → auth code → token exchange
                  → store access_token + refresh_token in Keychain/Keystore
                  → navigate to Hub
```

**Token refresh:** TanStack Query `onError` interceptor — on 401, attempt `POST /api/auth/refresh`; on failure, clear store and redirect to Login.

---

## Security controls on device

| Control | Implementation |
|---|---|
| No PII in AsyncStorage | All sensitive data in `expo-secure-store` (hardware-backed on Android) |
| Screenshot blocking | `expo-screen-capture.preventScreenCaptureAsync()` on Login + Proof Card |
| Biometric unlock | `expo-local-authentication`; fallback to PIN |
| Certificate pinning | `react-native-ssl-pinning` — pin to the bank's TLS leaf certificate |
| Jailbreak / root detection | `expo-device` checks; warn user, disable sensitive features |
| Clipboard protection | Never auto-copy financial figures |
| App backgrounding | Blur sensitive screens in the app switcher (iOS `UIApplicationProtectedDataAvailable`) |

---

## API contracts used (all shared with web)

| Screen | Endpoint | Method |
|---|---|---|
| Login | `/api/auth/demo-token` | POST |
| Hub, Proof Card | `/api/customers/{id}/opportunities` | GET |
| Feedback | `/api/customers/{id}/feedback` | POST |
| Insights opt-out | `/api/customers/{id}/insights-optout` | PUT |
| Health check | `/healthz` | GET |

All endpoints require `Authorization: Bearer <token>` except `/healthz`.
RBAC: `CUSTOMER` role — can read own opportunities only (`require_subject()` enforced server-side).

---

*This document is [DESIGN]. No React Native code exists. The same FastAPI contracts power both the Streamlit prototype and would power this app unchanged.*
