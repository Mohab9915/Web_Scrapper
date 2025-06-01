# Production Deployment Checklist

## 📋 Pre-Deployment Checklist

### Infrastructure Setup
- [ ] Supabase project created and configured
- [ ] Azure OpenAI resource deployed with required models
- [ ] Domain name registered (if applicable)
- [ ] SSL certificate obtained
- [ ] Hosting environment prepared (Docker, Kubernetes, Cloud)

### Database Setup
- [ ] All migrations applied in correct order
- [ ] pgvector extension enabled
- [ ] Database indexes created
- [ ] Row Level Security (RLS) policies configured
- [ ] Database backup strategy implemented

### Environment Configuration
- [ ] Production `.env` file created with real credentials
- [ ] All required environment variables set
- [ ] CORS origins configured for production domain
- [ ] API rate limiting configured
- [ ] Logging level set appropriately

### Security
- [ ] All default passwords changed
- [ ] API keys rotated and secured
- [ ] HTTPS enabled
- [ ] Security headers configured
- [ ] Input validation implemented
- [ ] SQL injection protection verified

### Application Features
- [ ] Web scraping functionality tested
- [ ] RAG system working with Azure OpenAI
- [ ] Chat functionality with title generation working
- [ ] File export features tested
- [ ] Real-time updates working
- [ ] Error handling implemented

## 🚀 Deployment Steps

### 1. Final Testing
```bash
# Run comprehensive tests
cd backend && python -m pytest tests/ -v
cd new-front && npm run test:ci

# Test build process
cd new-front && npm run build:prod
```

### 2. Database Migration
```bash
# Apply the conversation title migration
# Execute this SQL in your Supabase dashboard:
```
```sql
-- Update the conversation summary function to include titles
CREATE OR REPLACE FUNCTION get_project_conversations_summary(
    p_project_id UUID,
    p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
    conversation_id UUID,
    last_message_at TIMESTAMPTZ,
    preview TEXT,
    message_count BIGINT,
    title TEXT
) AS $$
BEGIN
    RETURN QUERY
    WITH conversation_stats AS (
        SELECT
            ch.conversation_id,
            MAX(ch.created_at) as last_message_at,
            COUNT(*) as message_count,
            -- Get the first user message as preview
            (
                SELECT ch2.message_content
                FROM chat_history ch2
                WHERE ch2.conversation_id = ch.conversation_id
                AND ch2.message_role = 'user'
                ORDER BY ch2.created_at ASC
                LIMIT 1
            ) as first_user_message,
            -- Get conversation title from system message metadata
            (
                SELECT ch3.metadata->>'conversation_title'
                FROM chat_history ch3
                WHERE ch3.conversation_id = ch.conversation_id
                AND ch3.message_role = 'system'
                AND ch3.metadata ? 'conversation_title'
                ORDER BY ch3.created_at DESC
                LIMIT 1
            ) as conversation_title
        FROM chat_history ch
        WHERE ch.project_id = p_project_id
        GROUP BY ch.conversation_id
    )
    SELECT
        cs.conversation_id,
        cs.last_message_at,
        CASE
            WHEN LENGTH(cs.first_user_message) > 100
            THEN LEFT(cs.first_user_message, 100) || '...'
            ELSE COALESCE(cs.first_user_message, 'No user messages')
        END as preview,
        cs.message_count,
        cs.conversation_title as title
    FROM conversation_stats cs
    ORDER BY cs.last_message_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
```

### 3. Environment Setup
```bash
# Copy and configure environment
cp .env.production .env
# Edit .env with your production values
```

### 4. Deploy
```bash
# Using Docker Compose
./deploy.sh production

# Or manually
docker-compose build --no-cache
docker-compose up -d
```

### 5. Verification
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost/health

# Check logs
docker-compose logs -f
```

## ✅ Post-Deployment Verification

### Functional Testing
- [ ] Frontend loads correctly
- [ ] User can create projects
- [ ] URL scraping works
- [ ] RAG system processes data
- [ ] Chat functionality works
- [ ] Chat titles generate automatically
- [ ] Data export works
- [ ] Real-time updates work

### Performance Testing
- [ ] Page load times acceptable
- [ ] API response times under 2 seconds
- [ ] Large data sets handle properly
- [ ] Memory usage within limits
- [ ] CPU usage reasonable

### Security Testing
- [ ] HTTPS working
- [ ] API authentication working
- [ ] No sensitive data in logs
- [ ] CORS properly configured
- [ ] Rate limiting working

## 🔧 Monitoring Setup

### Application Monitoring
- [ ] Health check endpoints responding
- [ ] Error tracking configured
- [ ] Performance monitoring setup
- [ ] Log aggregation working

### Infrastructure Monitoring
- [ ] Server resource monitoring
- [ ] Database performance monitoring
- [ ] Network monitoring
- [ ] Backup verification

## 📞 Emergency Procedures

### Rollback Plan
```bash
# Quick rollback to previous version
docker-compose down
git checkout previous-stable-tag
docker-compose up -d
```

### Emergency Contacts
- [ ] Database administrator contact
- [ ] Infrastructure team contact
- [ ] Application team contact
- [ ] Business stakeholder contact

### Incident Response
- [ ] Incident response plan documented
- [ ] Communication channels established
- [ ] Escalation procedures defined
- [ ] Recovery procedures tested

## 🎯 Success Criteria

### Technical Metrics
- [ ] 99.9% uptime target
- [ ] < 2 second API response time
- [ ] < 5 second page load time
- [ ] Zero critical security vulnerabilities

### Business Metrics
- [ ] User registration working
- [ ] Core features functional
- [ ] Data accuracy maintained
- [ ] User experience smooth

## 📝 Documentation

### User Documentation
- [ ] User guide updated
- [ ] API documentation current
- [ ] Feature documentation complete
- [ ] Troubleshooting guide available

### Technical Documentation
- [ ] Deployment guide current
- [ ] Architecture documentation updated
- [ ] Database schema documented
- [ ] API endpoints documented

## 🔄 Maintenance Plan

### Regular Tasks
- [ ] Weekly health checks
- [ ] Monthly security updates
- [ ] Quarterly performance reviews
- [ ] Annual disaster recovery tests

### Update Procedures
- [ ] Update testing process defined
- [ ] Deployment automation working
- [ ] Rollback procedures tested
- [ ] Change management process established

---

## 🎉 Deployment Complete!

Once all items are checked, your Interactive Agentic Web Scraper & RAG System with automatic chat title generation is ready for production use!

### Quick Access Links
- **Application**: https://yourdomain.com
- **API Docs**: https://yourdomain.com/api/docs
- **Health Check**: https://yourdomain.com/health
- **Admin Panel**: https://yourdomain.com/admin (if implemented)

### Support Information
- **Documentation**: See DEPLOYMENT.md
- **Issues**: GitHub Issues
- **Updates**: Follow deployment procedures in this checklist
