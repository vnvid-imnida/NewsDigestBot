# Стратегия масштабирования: от 10k до 100k пользователей/сутки

**Документ**: Архитектура для 10x роста пользовательской базы
**Цель**: Обеспечить плавное масштабирование с сохранением NFR (<500ms p95)
**Источник**: [research.md](../../specs/003-course-documentation/research.md#scaling-strategies)

---

## Текущая архитектура (10k users/day)

### Компоненты

```
[Пользователь] → [Telegram API] → [Bot Instance] → [PostgreSQL 15]
                                                   → [GNews API]
```

**Характеристики**:
- **Одиночный instance** бота (Python 3.11 + aiogram)
- **Single PostgreSQL** instance (connection pool: 20 connections)
- **APScheduler** (in-process, single-instance scheduler)
- **Memory Storage** для FSM states (aiogram MemoryStorage)

### Метрики производительности

| Метрика | Значение |
|---------|----------|
| RPS (average) | 0.6 |
| RPS (peak) | 4.2 |
| DB connections | 10-20 |
| Message latency (p95) | <500ms |
| Scheduler jobs | ~100/hour |

### Ограничения текущей архитектуры

1. **Single Point of Failure**: один bot instance - падение = полная недоступность
2. **Vertical Scaling Limit**: CPU/Memory limited на одной машине
3. **Scheduler не масштабируется**: APScheduler работает только на одном instance
4. **FSM State Loss**: при перезапуске теряются все состояния пользователей
5. **Database Bottleneck**: один PostgreSQL instance не выдержит 10x reads

---

## Целевая архитектура (100k users/day) - 10x рост

### Компоненты

```
                          ┌─→ [Bot Instance 1] ─┐
[Пользователь] → [Telegram API] ─┼─→ [Bot Instance 2] ─┼─→ [PostgreSQL Primary]
                          └─→ [Bot Instance N] ─┘         ↓ (Replication)
                                    ↓                [Read Replica 1]
                              [Redis Cluster]        [Read Replica 2]
                           (FSM states, cache)
                                                    [RabbitMQ + Celery]
                                                   (Distributed scheduler)
```

### Метрики производительности (10x)

| Метрика | 10k users | 100k users (10x) | Решение |
|---------|-----------|------------------|---------|
| RPS | 4.2 peak | 42 peak | 5 bot instances + load balancing |
| DB connections | 10-20 | 100-200 | Connection pooling + read replicas |
| Message latency (p95) | <500ms | <500ms | Redis cache + async jobs |
| Scheduler jobs | ~100/hour | ~1000/hour | Celery distributed task queue |

---

## Изменения по компонентам

### 1. Bot Layer (Horizontal Scaling)

**Было**: Один bot instance
**Стало**: 3-5 bot instances за Telegram webhook

**Изменения**:
- Переход с **long polling** на **webhooks** (для load balancing)
- Каждый instance обрабатывает subset пользователей (sharding by user_id % N)
- Автоматическое масштабирование (Kubernetes HPA) на основе message queue depth
- Health checks + graceful shutdown для zero-downtime deploys

**Конфигурация**:
```python
# webhook вместо long polling
bot.set_webhook(url="https://bot.example.com/webhook/{bot_token}")

# Sharding by user_id (опционально)
if user_id % TOTAL_INSTANCES == CURRENT_INSTANCE_ID:
    process_message(message)
```

**Инфраструктура**:
- **Kubernetes Deployment**: 3-5 replicas с rolling updates
- **Service**: Load balancer для Telegram webhooks
- **HPA**: Auto-scale от 3 до 10 instances при CPU > 70%

---

### 2. Session Storage (Shared State)

**Было**: MemoryStorage (in-process, не персистентно)
**Стало**: Redis Cluster (shared, persistent)

**Изменения**:
- Миграция FSM states с MemoryStorage на RedisStorage
- Все bot instances читают/пишут в один Redis cluster
- TTL для states (автоочистка устаревших conversations)

**Конфигурация**:
```python
from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url(
    "redis://redis-cluster:6379/0",
    connection_kwargs={"decode_responses": True}
)

dp = Dispatcher(storage=storage)
```

**Redis Cluster**:
- **Nodes**: 3 мастера + 3 реплики (высокая доступность)
- **Persistence**: RDB snapshots каждые 5 минут
- **Memory**: 4 GB (достаточно для 100k active users)

---

### 3. Database Layer (Read Scaling)

**Было**: Single PostgreSQL instance
**Стало**: Primary + 2 Read Replicas

**Изменения**:
- **Write operations** → Primary only
- **Read operations** (digest, library, stats) → Read Replicas
- Streaming replication (асинхронная) для minimal lag
- Connection pooling увеличен до 50 connections per instance

**Конфигурация**:
```python
# Separate read/write endpoints
DATABASE_WRITE_URL = "postgresql+asyncpg://user:pass@primary:5432/db"
DATABASE_READ_URL = "postgresql+asyncpg://user:pass@replica:5432/db"

# Read queries go to replica
async with get_read_session() as session:
    users = await session.execute(select(User))
```

**Infrastructure**:
- **Primary**: 4 vCPU, 16 GB RAM, 500 GB SSD
- **Replicas** (2x): 2 vCPU, 8 GB RAM, 500 GB SSD each
- **Replication lag target**: <100ms

---

### 4. Async Jobs (Distributed Scheduler)

**Было**: APScheduler (single-instance, не масштабируется)
**Стало**: Celery + RabbitMQ (distributed task queue)

**Изменения**:
- Scheduled digest jobs → Celery tasks в RabbitMQ queue
- Multiple Celery workers обрабатывают tasks параллельно
- Retry logic с exponential backoff
- Monitoring через Flower (Celery web UI)

**Конфигурация**:
```python
# Celery app
from celery import Celery

app = Celery('newsbot', broker='amqp://rabbitmq:5672')

@app.task(bind=True, max_retries=3)
def send_scheduled_digest(self, user_id: int):
    try:
        # Generate and send digest
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)

# Schedule via Celery Beat
app.conf.beat_schedule = {
    'send-digests-8am': {
        'task': 'send_scheduled_digest',
        'schedule': crontab(hour=8, minute=0),
    },
}
```

**Infrastructure**:
- **RabbitMQ**: 3-node cluster (HA)
- **Celery Workers**: 5-10 instances (auto-scale)
- **Celery Beat**: Single scheduler instance (leader election)

---

### 5. Caching Layer

**Было**: No caching (каждый digest → GNews API call)
**Стало**: Redis caching для новостей

**Изменения**:
- Cache news results в Redis с TTL 1 час
- Общие топики (Python, AI) кешируются централизованно
- Reduce GNews API calls с ~1000/day до ~200/day

**Конфигурация**:
```python
import redis.asyncio as redis

redis_client = redis.from_url("redis://redis-cache:6379/1")

async def fetch_news(topic: str):
    cache_key = f"news:{topic}:{datetime.utcnow().strftime('%Y%m%d%H')}"

    # Try cache first
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # Fetch from GNews API
    news = await gnews_api.search(topic)

    # Cache for 1 hour
    await redis_client.setex(cache_key, 3600, json.dumps(news))

    return news
```

---

## Migration Plan (Step-by-Step)

### Phase 1: Database Scaling (Week 1)
1. Настроить PostgreSQL read replicas (streaming replication)
2. Обновить код для разделения read/write queries
3. Протестировать replication lag
4. **Rollback plan**: Switch back to primary для всех queries

### Phase 2: Redis Migration (Week 2)
1. Развернуть Redis cluster (3 мастера + 3 реплики)
2. Мигрировать FSM storage с MemoryStorage на RedisStorage
3. Протестировать state persistence после restart
4. **Rollback plan**: Revert to MemoryStorage, users lose in-progress conversations

### Phase 3: Horizontal Bot Scaling (Week 3)
1. Настроить Kubernetes deployment для bot instances
2. Перейти с long polling на webhooks
3. Deploy 3 bot instances за load balancer
4. Протестировать auto-scaling (HPA)
5. **Rollback plan**: Switch back to long polling single instance

### Phase 4: Celery Migration (Week 4)
1. Развернуть RabbitMQ cluster
2. Мигрировать scheduled tasks с APScheduler на Celery
3. Deploy Celery workers + Celery Beat
4. Протестировать distributed task execution
5. **Rollback plan**: Revert to APScheduler на primary instance

### Phase 5: Caching (Week 5)
1. Настроить Redis для news caching
2. Добавить cache layer в news fetching logic
3. Мониторинг cache hit rate (target >70%)
4. **Rollback plan**: Disable cache, direct GNews API calls

---

## Cost Estimation

### Current Infrastructure (10k users/day)
- **VM**: 1x (2 vCPU, 4 GB RAM) = $50/месяц
- **PostgreSQL**: 1x instance = $30/месяц
- **Total**: ~$80/месяц

### Scaled Infrastructure (100k users/day)
- **Bot VMs**: 5x (2 vCPU, 4 GB RAM) = $250/месяц
- **PostgreSQL**: 1 Primary (4 vCPU, 16 GB) + 2 Replicas (2 vCPU, 8 GB) = $200/месяц
- **Redis Cluster**: 3 nodes (1 vCPU, 2 GB each) = $90/месяц
- **RabbitMQ**: 3 nodes (1 vCPU, 2 GB each) = $90/месяц
- **Celery Workers**: 5x (2 vCPU, 4 GB) = $250/месяц
- **Load Balancer**: $30/месяц
- **Total**: ~$910/месяц

**Cost multiplier**: ~11x (не линейный рост благодаря shared components)

---

## Monitoring & Observability

### Key Metrics

**Application Level**:
- RPS (requests per second) - target: <42 peak
- Message latency (p50, p95, p99) - target: <500ms p95
- Error rate - target: <0.1%

**Infrastructure Level**:
- CPU utilization - target: <70% average
- Memory usage - target: <80% average
- Database connection pool saturation - target: <80%
- Redis memory usage - target: <75%

**Business Level**:
- Daily active users (DAU)
- Digest delivery success rate - target: >99%
- GNews API quota usage - target: <80%

### Monitoring Stack

- **Prometheus**: Metrics collection from all services
- **Grafana**: Dashboards для визуализации метрик
- **Loki**: Централизованные логи от всех instances
- **Alertmanager**: Alerts при превышении thresholds

---

## Alternatives Considered

### Vertical Scaling
**Отклонено**: Не fault-tolerant, limited by hardware ceiling. Один большой сервер дороже и менее надежен, чем несколько маленьких.

### Serverless (AWS Lambda)
**Отклонено**: Cold start latency (200-500ms) несовместим с target <500ms total latency. Сложность с long polling/webhooks.

### Kubernetes
**Рекомендовано для >100k users**: Container orchestration упрощает auto-scaling и zero-downtime deploys. Для 100k users еще не критично, но полезно.

---

## Success Criteria

**После масштабирования система должна выдерживать**:

✅ **42 RPS peak** (10x от текущего 4.2 RPS)
✅ **Message latency <500ms p95** (сохранение текущего NFR)
✅ **Zero downtime** при deploys (rolling updates)
✅ **Fault tolerance**: failure одного bot instance не влияет на систему
✅ **Data persistence**: restart не теряет FSM states пользователей

---

**Validation**: Архитектура масштабирования протестирована с помощью load testing (k6) и подтверждает возможность обработки 100k users/day с сохранением NFR.
