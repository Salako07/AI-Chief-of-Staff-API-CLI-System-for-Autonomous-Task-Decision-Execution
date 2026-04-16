# Docker Deployment Guide

## Production-Ready Docker Stack

This deployment includes:
- **PostgreSQL**: Persistent idempotency logs and audit trail
- **Redis**: Celery message broker with persistence
- **FastAPI**: API server for processing requests
- **Celery Workers**: Background execution (2 replicas)
- **Flower**: Monitoring dashboard

## Quick Start

### 1. Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose v2.0+
- OpenAI API key

### 2. Configuration

Copy the environment template:

```bash
cp .env.docker .env
```

Edit `.env` and set:

```bash
# REQUIRED
OPENAI_API_KEY=sk-your-actual-key-here

# CHANGE IN PRODUCTION!
POSTGRES_PASSWORD=your_secure_postgres_password
REDIS_PASSWORD=your_secure_redis_password

# OPTIONAL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

### 3. Build and Start

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check all services are running
docker-compose ps

# Should show:
# ai_chief_postgres   Up (healthy)
# ai_chief_redis      Up (healthy)
# ai_chief_api        Up
# ai_chief_worker     Up
# ai_chief_flower     Up
```

### 5. Test the System

```bash
# Health check
curl http://localhost:8000/health

# Process request
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule meeting with John by Friday",
    "source": "email"
  }'
```

### 6. Access Monitoring

- **API**: http://localhost:8000
- **Flower** (Celery monitoring): http://localhost:5555
- **PostgreSQL**: localhost:5432
  - Database: `ai_chief_of_staff`
  - User: `ai_chief_user`
  - Password: (from .env)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │PostgreSQL│    │  Redis   │    │  Flower  │         │
│  │  :5432   │    │  :6379   │    │  :5555   │         │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘         │
│       │               │               │                 │
│  ┌────┴───────────────┴───────────────┘                │
│  │                                                      │
│  │  ┌──────────┐         ┌──────────┐                │
│  └─▶│   API    │         │ Worker x2│                │
│     │  :8000   │◀────────│          │                │
│     └──────────┘         └──────────┘                │
│                                                        │
└────────────────────────────────────────────────────────┘
          │                        │
          ▼                        ▼
     User Requests          Background Execution
                          (Slack, Email, etc.)
```

## Database Schema

### Executed Actions (Idempotency)

```sql
CREATE TABLE executed_actions (
    id UUID PRIMARY KEY,
    action_id VARCHAR(255) UNIQUE NOT NULL,
    action_hash VARCHAR(64) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    run_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE
);
```

### Processing Runs (Audit Trail)

```sql
CREATE TABLE processing_runs (
    run_id UUID PRIMARY KEY,
    input_text TEXT NOT NULL,
    tasks_count INTEGER,
    decisions_count INTEGER,
    risks_count INTEGER,
    quality_score INTEGER,
    processing_duration_ms INTEGER,
    status VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE
);
```

### Tasks, Decisions, Risks

Full schema in `init_db.sql`

## Management Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f postgres
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart api
docker-compose restart worker
```

### Scale Workers

```bash
# Scale to 5 workers
docker-compose up -d --scale worker=5

# Check worker status in Flower
open http://localhost:5555
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U ai_chief_user -d ai_chief_of_staff

# Run queries
\dt                                    # List tables
SELECT * FROM executed_actions LIMIT 10;
SELECT * FROM processing_runs LIMIT 10;

# Get execution stats
SELECT
    action_type,
    status,
    COUNT(*) as count
FROM executed_actions
GROUP BY action_type, status;
```

### Backup Database

```bash
# Backup
docker-compose exec postgres pg_dump -U ai_chief_user ai_chief_of_staff > backup.sql

# Restore
docker-compose exec -T postgres psql -U ai_chief_user ai_chief_of_staff < backup.sql
```

### Clear Old Logs

```bash
# Delete logs older than 90 days
docker-compose exec postgres psql -U ai_chief_user -d ai_chief_of_staff -c \
  "DELETE FROM executed_actions WHERE executed_at < NOW() - INTERVAL '90 days';"
```

## Monitoring

### Flower Dashboard

Access: http://localhost:5555

Features:
- Real-time task monitoring
- Worker status and statistics
- Task history and results
- Performance metrics
- Failed task investigation

### Health Checks

All services have health checks:

```bash
# Check health
docker-compose ps

# Healthy services show: Up (healthy)
# Unhealthy services show: Up (unhealthy)
```

### Logs Analysis

```bash
# Count executions by status
docker-compose logs worker | grep "Execution complete" | tail -20

# Find errors
docker-compose logs api | grep ERROR

# Check idempotency skips
docker-compose logs worker | grep SKIPPING
```

## Performance Tuning

### Worker Concurrency

Edit `.env`:

```bash
# Default: 4 concurrent tasks per worker
CELERY_WORKER_CONCURRENCY=8

# Restart workers
docker-compose restart worker
```

### PostgreSQL Performance

Edit `docker-compose.yml` postgres service:

```yaml
command: postgres -c shared_buffers=256MB -c max_connections=200
```

### Redis Memory

Edit `docker-compose.yml` redis service:

```yaml
command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

## Scaling for Production

### Horizontal Scaling

```yaml
# docker-compose.prod.yml
services:
  worker:
    deploy:
      replicas: 10  # 10 workers for high load
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

### Load Balancer

```yaml
# Add nginx for load balancing
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  depends_on:
    - api
```

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_executed_actions_created_at ON executed_actions(created_at DESC);
CREATE INDEX idx_processing_runs_status ON processing_runs(status);

-- Partition large tables by date (for millions of records)
CREATE TABLE executed_actions_202401 PARTITION OF executed_actions
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## Security

### Change Default Passwords

```bash
# Generate secure passwords
openssl rand -base64 32

# Update .env
POSTGRES_PASSWORD=<generated-password>
REDIS_PASSWORD=<generated-password>
```

### Environment Isolation

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use secrets management in production
# - AWS Secrets Manager
# - HashiCorp Vault
# - Docker Secrets
```

### Network Security

```yaml
# docker-compose.prod.yml
services:
  postgres:
    ports: []  # Don't expose postgres externally
    networks:
      - internal

  redis:
    ports: []  # Don't expose redis externally
    networks:
      - internal

  api:
    ports:
      - "8000:8000"  # Only expose API
    networks:
      - internal
      - external

networks:
  internal:
    internal: true
  external:
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Restart Docker
sudo systemctl restart docker
```

### Database Connection Failed

```bash
# Check postgres is healthy
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Verify password
docker-compose exec postgres psql -U ai_chief_user -d ai_chief_of_staff
```

### Worker Not Processing Tasks

```bash
# Check worker logs
docker-compose logs worker

# Check Redis connection
docker-compose exec worker redis-cli -h redis -a $REDIS_PASSWORD ping

# Restart worker
docker-compose restart worker
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.yml
services:
  worker:
    mem_limit: 2g
```

## Cleanup

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ DELETES DATA)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## Production Deployment

### AWS ECS/Fargate

```bash
# Build and push to ECR
docker build -t ai-chief-of-staff .
docker tag ai-chief-of-staff:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/ai-chief:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/ai-chief:latest

# Use managed services
# - RDS PostgreSQL
# - ElastiCache Redis
# - ECS for API and Workers
```

### Kubernetes

See `kubernetes/` directory for:
- Deployment manifests
- StatefulSets for databases
- Services and Ingress
- ConfigMaps and Secrets
- HorizontalPodAutoscaler

## Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify configuration: `.env` file
3. Check health: `docker-compose ps`
4. Review docs: `docs/` directory

## Next Steps

1. ✅ Deploy with Docker Compose
2. 📊 Monitor with Flower
3. 🔍 Query PostgreSQL for analytics
4. 🚀 Scale workers as needed
5. 🔒 Harden security for production
