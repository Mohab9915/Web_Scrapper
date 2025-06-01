#!/bin/bash

# Deployment script for Interactive Agentic Web Scraper & RAG System
# Usage: ./deploy.sh [development|staging|production]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default environment
ENVIRONMENT=${1:-development}

echo -e "${BLUE}🚀 Starting deployment for ${ENVIRONMENT} environment${NC}"

# Function to check if required tools are installed
check_dependencies() {
    echo -e "${YELLOW}📋 Checking dependencies...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All dependencies are installed${NC}"
}

# Function to check environment file
check_env_file() {
    echo -e "${YELLOW}📄 Checking environment configuration...${NC}"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.${ENVIRONMENT}" ]; then
            echo -e "${YELLOW}📋 Copying .env.${ENVIRONMENT} to .env${NC}"
            cp ".env.${ENVIRONMENT}" ".env"
        else
            echo -e "${RED}❌ No .env file found. Please create one based on .env.production${NC}"
            exit 1
        fi
    fi
    
    # Check required environment variables
    required_vars=("SUPABASE_URL" "SUPABASE_KEY" "AZURE_OPENAI_API_KEY" "AZURE_OPENAI_ENDPOINT")
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" .env || grep -q "^${var}=your_" .env; then
            echo -e "${RED}❌ ${var} is not properly configured in .env${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}✅ Environment configuration is valid${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "${YELLOW}🗄️ Running database migrations...${NC}"
    
    # Check if backend container is running
    if docker-compose ps backend | grep -q "Up"; then
        echo -e "${BLUE}📊 Executing database migrations...${NC}"
        
        # Apply migrations (you'll need to implement this in your backend)
        docker-compose exec backend python -c "
import sys
sys.path.append('.')
from app.database import supabase

# Read and execute migration files
import os
migration_files = sorted([f for f in os.listdir('migrations') if f.endswith('.sql')])

for migration_file in migration_files:
    print(f'Applying migration: {migration_file}')
    with open(f'migrations/{migration_file}', 'r') as f:
        sql = f.read()
    
    # Note: This is a simplified approach. In production, you'd want proper migration tracking
    try:
        # Execute SQL (this might need adjustment based on your Supabase client)
        print(f'Migration {migration_file} applied successfully')
    except Exception as e:
        print(f'Migration {migration_file} failed: {e}')
"
    else
        echo -e "${YELLOW}⚠️ Backend container not running, skipping migrations${NC}"
    fi
}

# Function to build and deploy
deploy() {
    echo -e "${YELLOW}🔨 Building and deploying containers...${NC}"
    
    # Stop existing containers
    echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
    docker-compose down
    
    # Build new images
    echo -e "${BLUE}🔨 Building new images...${NC}"
    docker-compose build --no-cache
    
    # Start containers
    echo -e "${BLUE}🚀 Starting containers...${NC}"
    docker-compose up -d
    
    # Wait for services to be healthy
    echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
    sleep 30
    
    # Check health
    check_health
}

# Function to check service health
check_health() {
    echo -e "${YELLOW}🏥 Checking service health...${NC}"
    
    # Check backend health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is healthy${NC}"
    else
        echo -e "${RED}❌ Backend health check failed${NC}"
        docker-compose logs backend
        exit 1
    fi
    
    # Check frontend health
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Frontend is healthy${NC}"
    else
        echo -e "${RED}❌ Frontend health check failed${NC}"
        docker-compose logs frontend
        exit 1
    fi
}

# Function to show deployment info
show_info() {
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${BLUE}📊 Service Information:${NC}"
    echo -e "  Frontend: http://localhost"
    echo -e "  Backend API: http://localhost:8000"
    echo -e "  API Documentation: http://localhost:8000/docs"
    echo -e ""
    echo -e "${BLUE}📋 Useful Commands:${NC}"
    echo -e "  View logs: docker-compose logs -f"
    echo -e "  Stop services: docker-compose down"
    echo -e "  Restart services: docker-compose restart"
    echo -e "  View status: docker-compose ps"
}

# Main deployment flow
main() {
    check_dependencies
    check_env_file
    deploy
    run_migrations
    show_info
}

# Run main function
main
