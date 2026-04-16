# Quick Start - Docker Deployment

## Prerequisites

- Docker Desktop or Docker Engine installed
- Docker Compose v2.0+
- OpenAI API key

## 1. Configure Environment

```bash
# The .env file is already created with test values
# Edit it to add your real OpenAI API key:
nano .env
```

**Required: Change this line:**
```bash
OPENAI_API_KEY=your-real-openai-key-here
```

**Optional: Change passwords for production:**
```bash
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_secure_password_here
```

## 2. Build & Start

```bash
# Build the Docker images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

## 3. Wait for Services (30-60 seconds)

Services need time to start and become healthy:
- PostgreSQL: ~10 seconds
- Redis: ~5 seconds
- API: ~20 seconds
- Worker: ~20 seconds
- Flower: ~15 seconds

Check status:
```bash
docker-compose ps
```

All services should show "Up" or "Up (healthy)"

## 4. Test the System

### Health Check
```bash
curl http://localhost:8000/health
```

Expected: `{"status":"healthy","service":"ai-chief-of-staff"}`

### Process a Request
```bash
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule meeting with John by Friday to discuss Q1 results. We decided to use Zoom.",
    "source": "test"
  }'
```

You should get a JSON response with extracted tasks and decisions!

## 5. Access Monitoring

- **API**: http://localhost:8000
- **Flower Dashboard**: http://localhost:5555
- **API Docs**: http://localhost:8000/docs

## 6. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker
docker-compose logs -f api
```

## 7. Check Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U ai_chief_user -d ai_chief_of_staff

# Run queries
SELECT * FROM executed_actions LIMIT 10;
SELECT * FROM processing_runs LIMIT 10;

# Exit
\q
```

## Common Commands

```bash
# Stop services
docker-compose down

# Restart services
docker-compose restart

# Scale workers
docker-compose up -d --scale worker=3

# View container stats
docker stats

# Clean everything (⚠️ deletes data)
docker-compose down -v
```

## Troubleshooting

### Services won't start
```bash
docker-compose logs
docker-compose ps
```

### Can't connect to API
```bash
# Check if API is running
docker-compose ps api

# Check API logs
docker-compose logs api

# Verify port 8000 is free
netstat -an | grep 8000
```

### Database errors
```bash
# Check postgres logs
docker-compose logs postgres

# Restart postgres
docker-compose restart postgres
```

## What's Running?

- **postgres**: PostgreSQL database on port 5432
- **redis**: Redis message broker on port 6379
- **api**: FastAPI server on port 8000
- **worker**: Celery worker (background tasks)
- **flower**: Monitoring dashboard on port 5555

## Next Steps

1. ✅ System is running!
2. 📊 Open Flower: http://localhost:5555
3. 🔍 Query database for analytics
4. 📝 Check DOCKER_DEPLOYMENT.md for advanced features
5. 🚀 Deploy to production

## Production Checklist

Before deploying to production:
- [ ] Change POSTGRES_PASSWORD
- [ ] Change REDIS_PASSWORD
- [ ] Set real OPENAI_API_KEY
- [ ] Configure SLACK_WEBHOOK_URL (optional)
- [ ] Review security settings
- [ ] Set up backups
- [ ] Configure monitoring/alerts

## Support

- Full docs: `DOCKER_DEPLOYMENT.md`
- Architecture: `docs/DEPLOYMENT_SUMMARY.md`
- Issues: Check logs with `docker-compose logs`
