#!/bin/bash

# FastAPI Docker startup script
# Usage: ./scripts/start.sh [--fast] [--build] [--down]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default flags
FAST=false
BUILD=false
DOWN=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fast)
            FAST=true
            shift
            ;;
        --build)
            BUILD=true
            shift
            ;;
        --down)
            DOWN=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./scripts/start.sh [--fast] [--build] [--down]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}FastAPI Docker Compose Manager${NC}"
echo -e "${BLUE}================================================${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi

# Shutdown existing services if --down flag
if [ "$DOWN" = true ]; then
    echo -e "${YELLOW}🛑 Stopping all services...${NC}"
    docker-compose down -v
    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
fi

# Create logs directory
mkdir -p logs
echo -e "${GREEN}✅ Logs directory created${NC}"

# If --fast flag, just start without rebuilding
if [ "$FAST" = true ]; then
    echo -e "${YELLOW}⚡ Starting services (fast mode - no rebuild)...${NC}"
    docker-compose up -d
    COMPOSE_EXIT=$?
else
    # Normal mode: build and start
    if [ "$BUILD" = true ]; then
        echo -e "${YELLOW}🔨 Building images and starting services...${NC}"
        docker-compose up -d --build
    else
        echo -e "${YELLOW}🚀 Starting services...${NC}"
        docker-compose up -d
    fi
    COMPOSE_EXIT=$?
fi

if [ $COMPOSE_EXIT -ne 0 ]; then
    echo -e "${RED}❌ Failed to start services${NC}"
    exit 1
fi

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 5

# Check service health
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Service Status${NC}"
echo -e "${BLUE}================================================${NC}"

# Check PostgreSQL
if docker-compose ps postgres | grep -q "Up"; then
    echo -e "${GREEN}✅ PostgreSQL${NC} - localhost:5432"
else
    echo -e "${RED}❌ PostgreSQL${NC} - Failed to start"
fi

# Check pgAdmin
if docker-compose ps pgadmin | grep -q "Up"; then
    echo -e "${GREEN}✅ pgAdmin${NC} - http://localhost:5050"
else
    echo -e "${RED}❌ pgAdmin${NC} - Failed to start"
fi

# Check Grafana
if docker-compose ps grafana | grep -q "Up"; then
    echo -e "${GREEN}✅ Grafana${NC} - http://localhost:3000"
else
    echo -e "${RED}❌ Grafana${NC} - Failed to start"
fi

# Check Loki
if docker-compose ps loki | grep -q "Up"; then
    echo -e "${GREEN}✅ Loki${NC} - http://localhost:3100"
else
    echo -e "${RED}❌ Loki${NC} - Failed to start"
fi

# Check Prometheus
if docker-compose ps prometheus | grep -q "Up"; then
    echo -e "${GREEN}✅ Prometheus${NC} - http://localhost:9090"
else
    echo -e "${RED}❌ Prometheus${NC} - Failed to start"
fi

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Access Points${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}FastAPI:${NC}      http://localhost:8000"
echo -e "${GREEN}pgAdmin:${NC}      http://localhost:5050/browser/"
echo -e "${GREEN}Grafana:${NC}      http://localhost:3000 (admin/admin123)"
echo -e "${GREEN}Prometheus:${NC}   http://localhost:9090"
echo -e "${GREEN}Loki:${NC}         http://localhost:3100"
echo -e "${GREEN}PostgreSQL:${NC}   localhost:5432"
echo ""
echo -e "${YELLOW}📋 View logs:${NC} docker-compose logs -f [service]"
echo -e "${YELLOW}🛑 Stop all:${NC}  ./scripts/start.sh --down"
echo -e "${BLUE}================================================${NC}"
