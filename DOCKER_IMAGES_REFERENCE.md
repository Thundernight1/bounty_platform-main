# Bounty Platform - Docker İmajları Referansı

## 📦 Proje İmajları (Kendi Build Ettiklerimiz)

| İmaj | Kaynak | Amaç | Dil | Boyut | Status |
|------|--------|------|-----|-------|--------|
| bounty_platform_backend | ./Dockerfile | FastAPI REST API sunucusu | Python 3.11 | 1.42GB | Production |
| bounty_platform_frontend | ./frontend/Dockerfile | React web arayüzü | Node.js 18 | 100MB | Production |
| bounty_platform_celery | ./Dockerfile | Async task worker | Python 3.11 | 1.42GB | Production |

## 🔧 Harici İmajlar (Docker Hub)

| İmaj | Sürüm | Amaç | Kontrol |
|------|-------|------|--------|
| postgres | 15-alpine | Relational database | db container |
| redis | 7-alpine | Cache & task queue | redis container |
| nginx | alpine | Reverse proxy | nginx container |
| prometheus | latest | Metrics collection | prometheus container |
| grafana | latest | Monitoring dashboard | grafana container |

## 🚀 Hızlı Komutlar

```bash
# Tüm imajları listele ve proje etiketlerine göre filtrele
docker images --filter "label=project=bounty-platform"

# Spesifik servisi kontrol et
docker ps --filter "label=project=bounty-platform"

# İmajın etiketlerini görüntüle
docker inspect bounty_platform_backend --format='{{json .Config.Labels}}'

# Proje ağını görüntüle
docker network inspect bounty_network
```

## 📊 Veri Hacmi Analizi

- **backend**: 1.42GB - Python dependencies ve application code
- **frontend**: 100MB - React build + nginx
- **database**: PostgreSQL alpine
- **cache**: Redis alpine
- **monitoring**: Prometheus + Grafana

## ⚙️ Service Haritası

```
┌─────────────────────────────────────┐
│         Nginx (Proxy)               │ :80, :443
└──────────┬──────────────────────────┘
           │
      ┌────┴───┐
      │         │
   Backend   Frontend
   :8000      :8080
      │         │
   ┌──┴─────────┴─┐
   │   Celery     │ 
   │   Worker     │
   └──┬───────────┘
      │
   ┌──┴────────────────────┐
   │                       │
Database            Redis  │
:5432             :6379   │
      │                   │
      └─── Monitoring ────┤
           Prometheus     │
           Grafana        │
```

## 🔍 Hangi İmaj Nerelerde Kullanılıyor?

### docker-compose.yml (Production)
- **backend** → FastAPI API
- **celery_worker** → Async tasks
- **frontend** → React UI
- **db** → PostgreSQL
- **redis** → Cache/queue
- **nginx** → Reverse proxy
- **prometheus** → Metrics
- **grafana** → Dashboard

### docker-compose.dev.yml (Development)
- **backend** → API + hot reload
- **db** → Dev database
- **redis** → Dev cache

---

**Son Güncelleme**: 2026-03-07
**Proje**: Bounty Platform
**Toplam İmaj Sayısı**: 8 (production) + 3 (dev)
