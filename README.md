# Payment Endpoint

Payment part of the online shop take-home task: a Flask + SQLAlchemy 2.0
HTTP endpoint that starts the payment for a cart, backed by PostgreSQL
with Alembic migrations and a mock payment provider.

Built with Flask 3, pure SQLAlchemy 2.0 (typed `Mapped` models, scoped
session) and plain Alembic. Dependency management via Poetry.

## What was built

1. **SQL schema for payments** — the `payments` table, added as an Alembic
   migration (`migrations/versions/f3a9c1d2e4b5_add_payments_table.py`) on
   top of the base schema, which is itself a migration
   (`b5e0a1c2d3f4_base_schema.py`, taken verbatim from the task-provided
   `SQLMigrations.sql`).
2. **HTTP endpoint** — `POST /carts/<cart_id>/payments` starts the payment
   for a cart (`payment_api/api/payments.py`).
3. **Mock payment provider** — `payment_api/services/provider.py`.
4. **Tests** — pytest suite in `tests/`, running against a real PostgreSQL.

## The endpoint

```
POST /carts/<cart_id>/payments
Content-Type: application/json            # body is optional
{"payment_method_id": "<uuid>"}           # optional: which saved card to charge
```

Flow (`payment_api/services/payment.py`):

1. Load the cart (404 `CART_NOT_FOUND`) and lock its row
   (`SELECT ... FOR UPDATE`) for the whole attempt.
2. Reject carts that are already `checked_out` (409
   `CART_ALREADY_CHECKED_OUT`) or `abandoned` (409 `CART_NOT_PAYABLE`).
3. Compute the total from the cart items (400 `EMPTY_CART`,
   409 `MIXED_CURRENCIES`).
4. Pick the card: the explicit `payment_method_id` (must belong to the
   cart's owner, 400 `PAYMENT_METHOD_NOT_FOUND`) or the user's default
   method (400 `NO_PAYMENT_METHOD`).
5. Create a `pending` payment row and call the mock provider.
6. On success: the payment becomes `succeeded` and the cart becomes
   `checked_out` — in the same transaction. On decline: the payment is
   recorded as `failed` (with the reason) and the cart stays `active`, so
   the user can retry.

Success — `201 Created`:

```json
{
  "payment_id": "...", "cart_id": "...", "user_id": "...",
  "amount": "70.00", "currency": "USD",
  "status": "succeeded", "provider": "mock",
  "provider_reference": "mock_charge_...",
  "created_at": "2026-11-05T12:00:00+00:00"
}
```

Declined — `402 Payment Required`; every error (validation included) uses
the same shape:

```json
{"error": {"code": "PAYMENT_FAILED", "message": "The payment provider declined the charge"}}
```

`GET /health` returns `{"status": "Healthy", "version": "..."}` and checks
the database connection.

## Mock payment provider

No real provider is connected (`payment_api/services/provider.py`). The
mock is deterministic: any provider token containing the fail marker
(default `fail`, e.g. `tok_fail_visa`) is declined, every other token
succeeds. The marker is configurable via `PROVIDER_FAIL_TOKEN_MARKER`.

## The payments table

| column               | type           | notes                                        |
|----------------------|----------------|----------------------------------------------|
| `id`                 | UUID PK        | `gen_random_uuid()`                          |
| `cart_id`            | UUID FK → carts| which cart is being paid                     |
| `user_id`            | UUID FK → users| denormalized owner for easy lookup           |
| `payment_method_id`  | UUID FK        | nullable, `ON DELETE SET NULL` (keep history)|
| `amount`             | NUMERIC(12, 2) | frozen at charge time                        |
| `currency`           | CHAR(3)        | default `USD`                                |
| `status`             | TEXT           | `pending` / `succeeded` / `failed`           |
| `provider`           | TEXT           | `mock`                                       |
| `provider_reference` | TEXT           | provider's charge id (only on success)       |
| `failure_reason`     | TEXT           | decline reason (only on failure)             |
| `created_at`/`updated_at` | TIMESTAMPTZ |                                          |

A **partial unique index** (`uq_payments_succeeded_cart ... WHERE status =
'succeeded'`) guarantees a cart can never be paid twice, while retries
after a decline stay possible. Indexed on `cart_id` and `user_id`.

## Assumptions

- **No authentication.** The task lists the user account as an existing
  part of the system and asks only for the payment part, so the endpoint
  is unauthenticated and derives the user from the cart.
- **Total calculation.** The "payment total calculation service" is given
  as existing; it is represented here by `CartTotalService`, which sums
  `quantity * unit_price` over the cart items (`unit_price` is frozen on
  the cart row, so later product price changes do not affect the charge).
- **Single currency per cart.** All items in a cart must share one
  currency; a mixed cart is rejected with 409 `MIXED_CURRENCIES` rather
  than silently converting.
- **Money is serialized as a string** (`"70.00"`) to avoid float rounding.
- **Card selection.** Without `payment_method_id` the user's default card
  (`is_default`) is charged. An explicit id must belong to the cart owner.
- **Retry semantics.** Only one payment attempt per request; a declined
  attempt is stored and the cart remains `active`, so retrying the same
  request is safe. A retried request after success gets 409, never a
  second charge (enforced by the cart row lock and the partial unique
  index).
- **Stock handling** is out of scope (payment part only).
- **Schema as migrations.** The whole schema lives in Alembic: the first
  migration applies the task-provided `SQLMigrations.sql` verbatim
  (including its sample data), and the payments table is added as a new
  migration on top, as the task requires. `alembic upgrade head` therefore
  works on an empty database.

## Run with Docker (recommended)

```bash
docker compose up --build        # Postgres + API; migrations (base schema
                                 # + payments) run automatically at start
```

The API is on http://127.0.0.1:8080. Try it with the seeded sample data:

```bash
# Alice's seeded cart (1 x Blue Kettle + 2 x Ceramic Mug = 70.00 USD)
curl -X POST http://127.0.0.1:8080/carts/c1c1c1c1-c1c1-c1c1-c1c1-c1c1c1c1c1c1/payments
# 201 {"amount": "70.00", "status": "succeeded", ...}

curl -X POST http://127.0.0.1:8080/carts/c1c1c1c1-c1c1-c1c1-c1c1-c1c1c1c1c1c1/payments
# 409 CART_ALREADY_CHECKED_OUT — a retry never charges twice
```

## Run locally

Requires a PostgreSQL server (or just the `db` compose service:
`docker compose up -d db`).

```bash
poetry install
make db-upgrade       # alembic upgrade head (base schema + payments table)
make run              # serves on http://0.0.0.0:8080 (PORT env var to change)
```

## Run the tests

```bash
make test             # starts the db container if needed, then pytest -v
```

The suite runs against a real PostgreSQL database (`payment_shop_test`,
created by the compose init scripts; override with `TEST_DATABASE_URI`).
It rebuilds the schema through the real migration path (`alembic upgrade
head`: base schema + payments table)
and truncates all tables between tests. It covers: the success path,
total calculation (quantities, frozen `unit_price`), exact public response
shape, every cart-state rejection (missing / checked-out / abandoned /
empty / mixed currencies), payment-method rules (missing default, foreign
method, malformed id), provider declines (recorded failure, cart stays
active), and a successful retry after a decline.

## Configuration (environment variables)

| Variable                    | Default                                                | Purpose                              |
|-----------------------------|--------------------------------------------------------|--------------------------------------|
| `DATABASE_URI`              | `postgresql+psycopg://postgres:postgres@localhost:5432/payment_shop` | SQLAlchemy database URI |
| `TEST_DATABASE_URI`         | same host, `payment_shop_test` database                | database used by the test suite      |
| `PROVIDER_FAIL_TOKEN_MARKER`| `fail`                                                 | mock provider decline marker         |
| `LOG_LEVEL`                 | `INFO`                                                 | logging level                        |
| `PORT`                      | `8080`                                                 | server port (`python server.py`)     |

## Project layout

```
server.py                  # dev entry point
SQLMigrations.sql          # provided base schema (reference; applied verbatim
                           #   by the first Alembic migration)
alembic.ini
migrations/                # Alembic env + base-schema and payments migrations
payment_api/
├── app.py                 # create_app factory
├── settings.py            # flat env-driven config
├── constants.py           # error codes/messages + CartStatus/PaymentStatus
├── exceptions.py          # {"error": {...}} exception hierarchy
├── error_handlers.py      # consistent JSON error responses
├── database/db.py         # engine + scoped session + Base (pure SQLAlchemy)
├── models/                # User, Product, Cart, CartItem, UserPaymentMethod, Payment
├── managers/              # cart, payment_method, payment
│                          #   (persistence only — select / add / commit)
├── services/              # payment (orchestration), cart_total, provider (mock), health
├── validators/            # payment_method_id format
├── data_classes/          # PaymentDetails / CartTotal / ProviderChargeResult DTOs
└── api/                   # base (health), payments handlers
│                          #   (request/response adapters only — no logic)
tests/                     # pytest + factory-boy
compose/                   # Dockerfile, entrypoint, db init scripts
```
