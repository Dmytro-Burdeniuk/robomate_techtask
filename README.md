# Опис вашого рішення тут

# Event Ingestion Service

Сервіс для прийому, зберігання та обробки подій користувачів із використанням **FastAPI**, **PostgreSQL**, **RabbitMQ**, **Redis** та **DuckDB**.

---

## Запуск

### 1. Клонування репозиторію

```bash
git clone https://github.com/Dmytro-Burdeniuk/robomate_techtask.git
cd backend-tech-task
```

### 2. Налаштування середовища

Створи `.env` файл:

```bash
DATABASE_URL=
REDIS_URL=
API_KEY=
RATE_LIMIT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
RABBITMQ_URL=
```

### 3. Запуск через Docker Compose

```bash
docker compose down -v --remove-orphans
docker compose build --no-cache
docker compose up -d
```

Очікувані сервіси:

* `event_api` — REST API (FastAPI)
* `event_worker` — RabbitMQ споживач
* `event_compactor` — DuckDB компактор (переносить старі дані)
* `events_db` — PostgreSQL
* `redis` — для rate limiting
* `rabbitmq` — брокер повідомлень

---

## Тестування та приклади

### Генератор даних

Генератор тестових подій:

```bash
docker exec -it event_api python -m app.benchmark
```

Вивід прикладу:

```
Inserted 100000 events in 0.13s
Throughput: 762921 events/sec
```

### Перевірка даних у базі

```bash
docker exec -it events_db psql -U postgres -d eventsdb
SELECT COUNT(*) FROM events;
```

### Перевірка воркера

```bash
docker logs -f event_worker
```

### Тестування ендпоінтів

Документація API доступна за адресою:

```
http://localhost:8000/docs
```

Приклади запитів:

```bash
curl -X POST http://localhost:8000/events \
  -H "X-API-KEY: yoursecretkey" \
  -H "Content-Type: application/json" \
  -d '[{"event_id": "uuid-1", "occurred_at": "2025-10-25T12:00:00Z", "user_id": "u1", "event_type": "login", "properties": {}}]'
```

---

## Ідемпотентність

Повторна відправка події з тим самим `event_id` не створює дублікати.
Реалізовано через використання `db.merge(event)` у SQLAlchemy — при повторному записі об'єкт із тим самим ID оновлюється, а не дублюється.

---

## Безпека та стабільність

* **Auth/ACL:** базовий `API-KEY` через FastAPI Depends.
* **Rate limit:** у пам’яті через Redis (token bucket).
* **Валідація:** вхідні дані перевіряються Pydantic схемами.
* **Обробка помилок:** повертаються структуровані HTTP коди.

---

## Черга повідомлень

Асинхронний інгест через **RabbitMQ**:

* retry на рівні `aio_pika` при збої з’єднання;
* dead-letter queue (`events_queue_dlq`) для невдалих повідомлень.

---

## Холодний/Гарячий шар (DuckDB)

* Нові події зберігаються у PostgreSQL.
* Події старші 7 днів компактуються у DuckDB (`cold_storage.duckdb`).
* Аналітика виконується по DuckDB без навантаження на PostgreSQL.

---

## Бенчмарк

### Методика

* Згенеровано **100 000 подій** з 6 типів (`login`, `logout`, `purchase` тощо).
* Дані надсилаються батчами по 1000 у `/events`.

### Без RabbitMQ

* Прямий запис у БД.
* ⏱ ~0.47s, ~214k events/sec.
* Вузьке місце — блокування PostgreSQL.

### З RabbitMQ

* Асинхронна публікація у чергу.
* ⏱ API-відповідь ~0.13s.
* Вузьке місце — швидкість обробки воркером.

---

## Спостережуваність

* **Структуровані логи:** FastAPI(MiddleWare).
* **Метрики:**

  * кількість подій/сек;
  * час обробки запиту;
  * кількість помилок.

---

## Тести

* Unit-тести для:

  * ідемпотентності;
  * індексації подій.
* Інтеграційний тест для повного циклу: *інгест → обробка → запит статистики*.

Запуск:

```bash
pytest -v
```

---

| Компонент      | Призначення       | Результат                  |
| -------------- | ----------------- | -------------------------- |
| **FastAPI**    | API               | швидкий інтерфейс          |
| **RabbitMQ**   | Черга повідомлень | асинхронна обробка         |
| **PostgreSQL** | Гарячі дані       | швидкий запис              |
| **DuckDB**     | Холодні дані      | аналітика без навантаження |
| **Redis**      | Rate limit        | стабільність               |

