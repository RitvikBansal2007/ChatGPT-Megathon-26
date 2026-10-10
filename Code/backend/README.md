# GreenProof Core Backend & Database Foundation

This package provides the core transactional backend, relational persistence, and REST API foundation for the GreenProof application.

---

## 1. Architecture & Data Flow

```text
HTTP Request
     │
     ▼
[ FastAPI App (app.py) ]
     │ (CORS, Safe Error Handlers, Liveness/Readiness)
     ▼
[ Auth Boundary (dependencies.py) ]
     │ (Bearer Token Check -> AuthenticatedUser)
     ▼
[ Transaction Router (routers/transactions.py) ]
     │ (Pydantic Schema Validation & Customer Ownership Scoping)
     ▼
[ Repository Layer (repository.py) ]
     │ (Parameterized SQL, Atomic Savepoints, Decimal Integrity)
     ▼
[ SQLite Database (db.py + schema.sql) ]
     │ (Foreign Keys Enabled, ON DELETE RESTRICT)
     ▼
(Local Storage / In-Memory)
```

---

## 2. Module Responsibilities

* **`Code/backend/config.py`**: Validated application settings using `pydantic-settings`. Enforces security invariants (e.g. production requires `AUTH_ENABLED=True`, bans wildcard CORS, and validates JWT secrets without leaking values).
* **`Code/backend/db.py`**: Thread-safe SQLite connection factory (`check_same_thread=False`), connection manager with guaranteed cleanup, and schema DDL migration runner.
* **`Code/backend/schema.sql`**: SQLite relational schema defining `users` and `transactions` tables, indexes, and foreign key constraints (`ON DELETE RESTRICT`).
* **`Code/backend/repository.py`**: Data access object (DAO) ensuring zero raw SQL in route handlers. Manages user records, transaction records, real calendar date validation, decimal precision preservation, canonical category checks, and atomic CSV savepoint imports.
* **`Code/backend/api/app.py`**: FastAPI application factory, CORS middleware configuration, global exception sanitization, and health check routes.
* **`Code/backend/api/dependencies.py`**: Request-scoped database connection lifecycle management (guaranteed commit/rollback/close) and the pluggable authentication boundary.
* **`Code/backend/api/schemas.py`**: Pydantic v2 request and response models with strict validations and field prohibition.
* **`Code/backend/api/routers/transactions.py`**: REST endpoints enforcing customer ownership scoping on every read and write operation.

---

## 3. Environment Variables

| Variable | Description | Default | Production Requirement |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Application mode (`development`, `test`, `production`) | `development` | Must be `production` |
| `GREENPROOF_DB_PATH` | Path to SQLite database file | Local `greenproof.db` | Outside tracked source tree |
| `AUTH_ENABLED` | Toggle for authentication enforcement | `False` | **Must be `True`** |
| `JWT_SECRET_KEY` | Symmetric key for JWT verification | `None` | **Required**, $\ge 32$ chars, non-placeholder |
| `CORS_ORIGINS` | Comma-separated allowed web origins | `http://localhost:3000,http://127.0.0.1:3000` | Explicit production domain (no `*`) |
| `RATE_LIMIT_PER_MINUTE` | Request throttling limit | `60` | Positive integer $> 0$ |
| `PSEUDONYM_KEY` | HMAC key for identifier pseudonymisation | None | Required when pseudonymising |

---

## 4. Local Development Setup

Ensure Python 3.11+ is active with the required project dependencies:

```bash
# Verify Python version
python3 --version

# Copy the sample environment file
cp .env.example .env
```

---

## 5. Running the API Locally

Run the development server using Uvicorn:

```bash
PYTHONPATH=Code uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI documentation is available in development mode at:
* Swagger UI: `http://127.0.0.1:8000/docs`

---

## 6. Running Tests

Run the backend and integration test suites:

```bash
# Run all backend unit and API tests
python3 -m pytest Code/tests/unit/test_config.py Code/tests/unit/test_backend_db.py Code/tests/unit/test_api.py -v

# Run the complete test suite including carbon calculation and privacy gates
python3 -m pytest Code/tests/unit/ -v
```

---

## 7. Supported Endpoints

### `GET /health`
* **Auth Required:** No
* **Response (200):**
```json
{
  "status": "ok",
  "environment": "development"
}
```

### `GET /ready`
* **Auth Required:** No
* **Response (200):**
```json
{
  "status": "ok",
  "environment": "development"
}
```

### `POST /api/v1/transactions`
* **Auth Required:** Yes (`Authorization: Bearer <token>`)
* **Request Body:**
```json
{
  "date": "2026-06-15",
  "description": "Octopus Energy Elec",
  "amount": "112.50",
  "currency": "GBP",
  "debit_credit": "debit",
  "category": "Electricity"
}
```
* **Response (201 Created):**
```json
{
  "transaction_id": "TXN-8F7B3E12D041",
  "user_id": "CUST-0001",
  "date": "2026-06-15",
  "description": "Octopus Energy Elec",
  "amount": "112.50",
  "currency": "GBP",
  "debit_credit": "debit",
  "category": "Electricity",
  "import_batch_id": null,
  "created_at": "2026-10-11 01:00:00.000"
}
```

### `GET /api/v1/transactions`
* **Auth Required:** Yes (`Authorization: Bearer <token>`)
* **Response (200 OK):**
```json
{
  "transactions": [
    {
      "transaction_id": "TXN-8F7B3E12D041",
      "user_id": "CUST-0001",
      "date": "2026-06-15",
      "description": "Octopus Energy Elec",
      "amount": "112.50",
      "currency": "GBP",
      "debit_credit": "debit",
      "category": "Electricity",
      "import_batch_id": null,
      "created_at": "2026-10-11 01:00:00.000"
    }
  ],
  "count": 1
}
```

### `GET /api/v1/transactions/{transaction_id}`
* **Auth Required:** Yes (`Authorization: Bearer <token>`)
* **Response (200 OK):** Single `TransactionResponse`
* **Response (404 Not Found):** Returned if the transaction does not exist OR belongs to another customer (deny-by-default).

### `POST /api/v1/transactions/import`
* **Auth Required:** Yes (`Authorization: Bearer <token>`)
* **Content-Type:** `multipart/form-data`
* **Form Fields:** `file` (CSV file, $\le 5$ MB), `currency` (optional, e.g. `GBP`).
* **Expected CSV Format:**
```csv
date,description,amount
2026-05-10,Supermarket Fuel,55.00
2026-05-12,Train Ticket,24.50
```
* **Response (200 OK):**
```json
{
  "imported_count": 2,
  "import_batch_id": "import_a4b91c20"
}
```

---

## 8. Validation & Consistency Rules

1. **Monetary Precision:** Stored strictly as validated decimal strings (`TEXT`) in SQLite matching `^-?\d+(\.\d+)?$`. Floating-point conversion and silent rounding are strictly prevented.
2. **Calendar Dates:** Format must be `YYYY-MM-DD` and represent a real calendar date via `datetime.date.fromisoformat` (e.g. `2026-02-31` is rejected with 422).
3. **Descriptions:** Must be non-empty string between 1 and 255 characters; whitespace-only values are rejected.
4. **Canonical Categories:** Restricted to the 8 project categories defined in `Code/config/categories.yaml`:
   * `Fuel`, `Electricity`, `Gas`, `Public Transport`, `Home Improvement`, `Automotive`, `Utilities`, `Other`.
5. **Currency Handling:** Preserved as supplied (or `NULL` if omitted). Never implicitly defaulted to GBP.
6. **Atomic Rollback Guarantee:** CSV imports run inside an isolated SQLite `SAVEPOINT`. If any row fails validation, the entire batch rolls back, leaving zero partial rows in the database.

---

## 9. Customer Ownership & Privacy Boundaries

* **No Client-Supplied User IDs:** The API never trusts a `user_id` passed in request payloads or URL parameters. All operations are strictly bound to `current_user.user_id` resolved from the verified authentication boundary.
* **Customer Isolation:** Customers cannot view or modify transactions belonging to any other customer. Attempting to look up another customer's transaction returns HTTP 404.
* **LLM Privacy Boundary:** Raw transaction descriptions and personal identifiers are never forwarded to language models. All future AI flows must route payloads through `Code/security/privacy.py:scrub_text` and `llm_payload`.

---

## 10. Implemented vs. Pending Security Controls

### Implemented Controls
* Validated configuration with environment-specific invariants.
* Production fail-closed protections (bans `*` CORS, requires `AUTH_ENABLED=True`, requires strong secrets).
* Masked secret representations via `SecretStr`.
* Parameterized SQL queries preventing SQL injection.
* Foreign-key integrity with `ON DELETE RESTRICT`.
* Atomic CSV import with bounded payload size ($\le 5$ MB).
* Sanitized global error handlers preventing stack trace and query leakage.
* Double-blind policy compliance (zero personal names in codebase).

### Controls Pending Security Team Integration
* **JWT Signature Verification:** The authentication boundary in `dependencies.py` is defined, but actual cryptographic token verification awaits the security team's JWT verifier.
* **Role-Based Access Control (RBAC):** Roles (`customer`, `analyst`, `admin`) are prepared on the `AuthenticatedUser` model, awaiting confirmation of permission hierarchies.
* **Active Rate Limiting:** The `RATE_LIMIT_PER_MINUTE` setting is validated in configuration, but rate-limiting middleware is not yet attached to the ASGI pipeline.
* **Database At-Rest Encryption:** SQLite runs in standard encrypted-filesystem mode; SQLCipher is not configured.

---

## 11. Authentication Integration Checklist for Security Lead

To connect the security team's authentication implementation:

1. Confirm the JWT signing algorithm (`HS256`) and agreed claims (`sub` for user ID, `role`, `exp`).
2. Provide the token verification function matching:
   ```python
   def verify_token(token: str) -> AuthenticatedUser:
       ...
   ```
3. Register the provider using `backend.api.dependencies.set_auth_provider(verify_token)`.
4. Confirm the unified source for `PSEUDONYM_KEY` and whether it should be read from `Settings`.
