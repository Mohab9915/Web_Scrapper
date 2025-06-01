# Deployment Guide - Interactive Agentic Web Scraper & RAG System

This guide covers deployment options for the Interactive Agentic Web Scraper & RAG System with automatic chat title generation.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Supabase account and project
- Azure OpenAI account and deployment

### 1. Environment Setup

1. Copy the environment template:
```bash
cp .env.production .env
```

2. Edit `.env` with your actual credentials:
```bash
# Required: Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Required: Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_CHAT_MODEL=gpt-4o
AZURE_EMBEDDING_MODEL=text-embedding-ada-002
```

### 2. Database Setup

1. In your Supabase dashboard, run the SQL from `backend/migrations/` in order:
   - `01_initial_schema.sql`
   - `02_project_urls_table.sql`
   - `03_add_formatted_tabular_data.sql`
   - `04_add_caching_enabled.sql`
   - `05_add_rag_enabled_to_project_urls.sql`
   - `06_create_chat_history_table.sql`
   - `07_add_conversation_functions.sql`
   - `08_add_url_status_and_last_session_id.sql`
   - `09_add_pagination_data.sql`
   - `10_create_scraped_data_table.sql`

2. Enable the pgvector extension in Supabase:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. Deploy with Docker

Run the deployment script:
```bash
./deploy.sh production
```

Or manually:
```bash
docker-compose up -d
```

### 4. Access Your Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Deployment Options

### Option 1: Docker Compose (Recommended)

**Pros**: Easy setup, good for small to medium deployments
**Cons**: Single server, limited scalability

```bash
# Development
./deploy.sh development

# Production
./deploy.sh production
```

### Option 2: Kubernetes

**Pros**: Highly scalable, production-ready, auto-healing
**Cons**: More complex setup

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s-deployment.yaml

# Update secrets with your values
kubectl edit secret scrapemaster-secrets -n scrapemaster
```

### Option 3: Cloud Platforms

#### Vercel (Frontend) + Railway/Render (Backend)

1. **Frontend on Vercel**:
   - Connect your GitHub repository
   - Set build command: `cd new-front && npm run build:prod`
   - Set output directory: `new-front/build`

2. **Backend on Railway**:
   - Connect repository
   - Set start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add environment variables

#### AWS/GCP/Azure

Use the provided Docker images with your preferred container service:
- AWS ECS/Fargate
- Google Cloud Run
- Azure Container Instances

## 🔒 Security Considerations

### Production Checklist

- [ ] Use HTTPS in production
- [ ] Set strong database passwords
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up monitoring and logging
- [ ] Regular security updates
- [ ] Backup strategy

### Environment Variables Security

Never commit `.env` files to version control. Use:
- Docker secrets
- Kubernetes secrets
- Cloud provider secret managers

## 📊 Monitoring

### Health Checks

- Backend: `GET /health`
- Frontend: `GET /health`

### Logs

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Metrics

Monitor these key metrics:
- Response times
- Error rates
- Memory usage
- CPU usage
- Database connections

## 🔄 Updates and Maintenance

### Updating the Application

1. Pull latest changes:
```bash
git pull origin main
```

2. Rebuild and deploy:
```bash
./deploy.sh production
```

### Database Migrations

New migrations are automatically applied during deployment. For manual application:

```bash
docker-compose exec backend python -c "
# Run migration script
"
```

### Backup Strategy

1. **Database**: Use Supabase automatic backups
2. **Application Data**: Regular exports via API
3. **Configuration**: Version control all config files

## 🐛 Troubleshooting

### Common Issues

1. **Backend won't start**:
   - Check environment variables
   - Verify Supabase connection
   - Check logs: `docker-compose logs backend`

2. **Frontend can't connect to backend**:
   - Verify CORS settings
   - Check network connectivity
   - Verify API endpoints

3. **Database connection issues**:
   - Verify Supabase credentials
   - Check network connectivity
   - Verify database schema

### Debug Commands

```bash
# Check container status
docker-compose ps

# Access backend container
docker-compose exec backend bash

# Access frontend container
docker-compose exec frontend sh

# View real-time logs
docker-compose logs -f --tail=100
```

## 📞 Support

For deployment issues:
1. Check the logs first
2. Verify all environment variables
3. Ensure database migrations are applied
4. Check network connectivity

## 🎯 Performance Optimization

### Production Optimizations

1. **Frontend**:
   - Enable gzip compression
   - Use CDN for static assets
   - Implement caching headers

2. **Backend**:
   - Use connection pooling
   - Implement Redis caching
   - Optimize database queries

3. **Database**:
   - Add appropriate indexes
   - Regular maintenance
   - Monitor query performance

### Scaling

- **Horizontal**: Add more container instances
- **Vertical**: Increase container resources
- **Database**: Use read replicas for heavy read workloads
