# User Management API

REST API สำหรับจัดการข้อมูลผู้ใช้ (`users`)  
Stack: FastAPI + SQLAlchemy + PostgreSQL + Alembic + Docker

## Features

- CRUD user : (`GET / list`, `GET /:id`, `POST`, `PUT`, `DELETE`)
- health check (`GET /health`)
- ค้นหา `q` จาก `name` หรือ `email` (apply เมื่อ `q` ยาว >= 3)
- pagination ด้วย `start` และ `limit` พร้อม metadata (`total`, `page`, `total_pages`)
- validation:
  - `age` ต้องเป็นตัวเลข (`StrictInt`)
  - `email` ต้องรูปแบบถูกต้อง + ไม่ซ้ำ
  - `name` และ `avatarUrl` ห้ามว่าง
- soft delete (`deleted_at`) 

## Project Structure

```text
app/
  api/            # routes + dependency injection
  services/       # business logic
  repositories/   # database queries
  schemas/        # request/response validation
  models/         # SQLAlchemy models
  db/             # base + session
  core/           # config
alembic/          # migrations
test_app.py       # automated API tests
```

## Run (Docker - recommended)

```bash
docker compose up --build
```

- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Stop: `docker compose down`
- Stop + remove volume: `docker compose down -v`

## Run (Local)

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/user_management_api"
alembic upgrade head
uvicorn app.main:app --reload
```

## API Endpoints

- `GET /health`
- `GET /api/user?q=&start=0&limit=10`
- `GET /api/user/{userId}`
- `POST /api/user`
- `PUT /api/user/{userId}`
- `DELETE /api/user/{userId}`

### Pagination Response Shape

`GET /api/user` จะคืนค่าเป็น:

```json
{
  "items": [
    {
      "id": 1,
      "name": "Alice",
      "age": 29,
      "email": "alice@example.com",
      "avatarUrl": "https://example.com/alice.png"
    }
  ],
  "total": 1,
  "page": 1,
  "total_pages": 1
}
```

## Delete Behavior

- ลบครั้งแรก: `{ "status": "success" }`
- ลบซ้ำ/ไม่พบ: `{ "status": "failed", "message": ... }`

## Error Handling

- `422` invalid input
- `409` duplicate email
- `500` unexpected error:

```json
{
  "status": "failed",
  "message": "Unexpected server error"
}
```

## Automated Tests

มีชุดทดสอบใน `test_app.py` (pytest + FastAPI TestClient) ครอบคลุมทั้ง correctness และ edge cases เช่น:

- create user success
- duplicate email
- invalid email / invalid payload shape
- pagination
- delete ซ้ำ
- pagination metadata correctness
- search policy (`q` สั้นกว่า 3 ตัว และ contains search เมื่อ `q` ยาวพอ)

รันเทสต์:

```bash
python3 -m pytest -q
```

## Highlights

- ใช้ layered architecture (`route -> service -> repository`) + Dependency Injection เพื่อแยก concern ชัดและรองรับการทดสอบ
- ออกแบบ validation แบบ fail-fast ใน schema (`StrictInt`, regex email, sanitize input) และ normalize email ก่อนเข้าฐานข้อมูล
- รองรับ concurrency เรื่อง email ซ้ำด้วย DB unique constraint + จัดการ `IntegrityError` ให้เป็น `409 Conflict`
- คุม performance ของ search/pagination: minimum query length, field projection (`load_only`), และมี index strategy สำหรับ PostgreSQL
- จัด API contract ให้ frontend-friendly ด้วย pagination metadata (`items`, `total`, `page`, `total_pages`)

## Demo

> กรณีรันผ่าน Docker ให้เปิดระบบก่อน: `docker compose up --build`

```bash
# 1) health check
curl -i http://127.0.0.1:8000/health

# 2) create user (success)
curl -i -X POST http://127.0.0.1:8000/api/user \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice",
    "age": 29,
    "email": "alice@example.com",
    "avatarUrl": "https://example.com/alice.png"
  }'

# 3) create user (validation error: invalid email)
curl -i -X POST http://127.0.0.1:8000/api/user \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bad Email",
    "age": 30,
    "email": "not-an-email",
    "avatarUrl": "https://example.com/bad.png"
  }'

# 4) list + pagination
curl -i "http://127.0.0.1:8000/api/user?start=0&limit=2"

# 5) soft delete behavior (replace {id} with real id)
curl -i -X DELETE http://127.0.0.1:8000/api/user/{id}

# 6) automated tests
python3 -m pytest -q
```

### Required CLI Evidence (Screenshots)

เก็บรูปใน `docs/screenshot/`:

| No. | Scenario | Evidence | Input / Expected / Actual |
|---|---|---|---|
| 1 | Health check | [docs/screenshot/01-cli-health-check.png](docs/screenshot/01-cli-health-check.png) | `curl /health` -> expected `200`, actual `200` |
| 2 | Create user success | [docs/screenshot/02-cli-create-user-success.png](docs/screenshot/02-cli-create-user-success.png) | valid JSON -> expected `status=success`, actual `status=success` |
| 3 | Validation error | [docs/screenshot/03-cli-create-user-validation-error.png](docs/screenshot/03-cli-create-user-validation-error.png) | invalid email -> expected `422`, actual `422` |
| 4 | List + pagination | [docs/screenshot/04-cli-list-pagination.png](docs/screenshot/04-cli-list-pagination.png) | `start=0&limit=2` -> expected `items + total/page/total_pages`, actual matched |
| 5 | Soft delete behavior | [docs/screenshot/05-cli-delete-soft-delete.png](docs/screenshot/05-cli-delete-soft-delete.png) | delete same id twice -> expected success then failed, actual matched |
| 6 | Automated tests | [docs/screenshot/06-cli-test-suite-pass.png](docs/screenshot/06-cli-test-suite-pass.png) | run `pytest` -> expected all pass, actual all pass |
| 7 | Docker runtime | [docs/screenshot/07-cli-docker-compose-up.png](docs/screenshot/07-cli-docker-compose-up.png) | run compose -> expected services healthy, actual healthy |
| 8 | Swagger UI (optional reference) | [docs/screenshot/Swagger-UI.png](docs/screenshot/Swagger-UI.png) | contract view for quick endpoint verification |

### Video Demo 

วิดีโอเดโม (ไฟล์ในโปรเจกต์):

- [docs/demo/create-list-delete.mov](docs/demo/create-list-delete.mov)
- [docs/demo/error-handling.mov](docs/demo/error-handling.mov)


## Implementation Trade-offs

- ใช้ `offset pagination` ตามโจทย์ที่ต้องรองรับการไปหน้าอื่น (page jump) (แม้รู้ว่า keyset pagination scale ดีกว่าในหน้าลึกหรือการเปิดโหลดเยอะๆ)
- search จะ apply เมื่อ `q` ยาวอย่างน้อย 3 ตัว เพื่อลด query กว้างเกินจำเป็นและลด load บน DB
- ใช้ contains search (`%keyword%`) เพื่อให้ผลลัพธ์ค้นหาไม่ตกหล่น เช่น `my-alice`
- เพิ่ม PostgreSQL `pg_trgm + GIN` index บน `lower(name)` และ `lower(email)` เพื่อชดเชย cost ของ contains search จุดนี้แม้จะเสียพื้นที่ Index และ cost time ตอน insert/update แต่ก็คุ้มค่ากว่าหาก project โตขึ้น
