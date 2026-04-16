#!/bin/bash

# Test script for Docker deployment
set -e

echo "=========================================="
echo "AI Chief of Staff - Docker Deployment Test"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please copy .env.docker to .env and configure it"
    exit 1
fi

# Check if OpenAI API key is set
if ! grep -q "sk-" .env; then
    echo -e "${RED}Error: OPENAI_API_KEY not set in .env${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 1: Building Docker images...${NC}"
docker-compose build

echo -e "\n${YELLOW}Step 2: Starting services...${NC}"
docker-compose up -d

echo -e "\n${YELLOW}Step 3: Waiting for services to be healthy (60s)...${NC}"
sleep 60

echo -e "\n${YELLOW}Step 4: Checking service status...${NC}"
docker-compose ps

# Check if postgres is healthy
if docker-compose ps postgres | grep -q "healthy"; then
    echo -e "${GREEN}✓ PostgreSQL is healthy${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not healthy${NC}"
    docker-compose logs postgres
    exit 1
fi

# Check if redis is healthy
if docker-compose ps redis | grep -q "healthy"; then
    echo -e "${GREEN}✓ Redis is healthy${NC}"
else
    echo -e "${RED}✗ Redis is not healthy${NC}"
    docker-compose logs redis
    exit 1
fi

# Check if api is running
if docker-compose ps api | grep -q "Up"; then
    echo -e "${GREEN}✓ API is running${NC}"
else
    echo -e "${RED}✗ API is not running${NC}"
    docker-compose logs api
    exit 1
fi

# Check if worker is running
if docker-compose ps worker | grep -q "Up"; then
    echo -e "${GREEN}✓ Worker is running${NC}"
else
    echo -e "${RED}✗ Worker is not running${NC}"
    docker-compose logs worker
    exit 1
fi

echo -e "\n${YELLOW}Step 5: Testing API health endpoint...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API health check passed${NC}"
else
    echo -e "${RED}✗ API health check failed${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Step 6: Testing processing endpoint...${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Schedule meeting with John by Friday to discuss Q1 results",
    "source": "test"
  }')

if echo "$RESPONSE" | grep -q "run_id"; then
    echo -e "${GREEN}✓ Processing endpoint works${NC}"
    echo "Response: $RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
else
    echo -e "${RED}✗ Processing endpoint failed${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

echo -e "\n${YELLOW}Step 7: Checking database...${NC}"
DB_CHECK=$(docker-compose exec -T postgres psql -U ai_chief_user -d ai_chief_of_staff -c "SELECT COUNT(*) FROM executed_actions;" 2>&1)
if echo "$DB_CHECK" | grep -q "count"; then
    echo -e "${GREEN}✓ Database is accessible${NC}"
    echo "$DB_CHECK"
else
    echo -e "${RED}✗ Database check failed${NC}"
    echo "$DB_CHECK"
fi

echo -e "\n${YELLOW}Step 8: Checking worker logs...${NC}"
docker-compose logs --tail=20 worker

echo -e "\n${GREEN}=========================================="
echo "All tests passed! ✓"
echo "==========================================${NC}"

echo -e "\n${YELLOW}Access points:${NC}"
echo "- API: http://localhost:8000"
echo "- Flower (monitoring): http://localhost:5555"
echo "- PostgreSQL: localhost:5432"

echo -e "\n${YELLOW}Useful commands:${NC}"
echo "- View logs: docker-compose logs -f"
echo "- Stop services: docker-compose down"
echo "- Restart services: docker-compose restart"
