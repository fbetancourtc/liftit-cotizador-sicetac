# 🚀 Production Deployment Guide - SICETAC Quotation Platform

## Overview

This guide provides complete instructions for deploying the SICETAC quotation platform to production servers.

## 📋 Pre-Deployment Checklist

- [ ] Production server with Ubuntu 20.04+ or similar
- [ ] Docker and Docker Compose installed
- [ ] Domain name configured (e.g., sicetac.liftit.com)
- [ ] SICETAC production credentials from Ministry of Transport
- [ ] Supabase project for authentication (optional)
- [ ] SSL certificate or Let's Encrypt setup
- [ ] Minimum 2GB RAM, 20GB storage

## 🏗️ Production Architecture

```
┌─────────────┐     ┌──────────┐     ┌────────────┐
│   Nginx     │────▶│   App    │────▶│ PostgreSQL │
│  (Reverse   │     │ (FastAPI)│     │ (Database) │
│   Proxy)    │     └──────────┘     └────────────┘
└─────────────┘            │
       │                   ▼
       │            ┌──────────┐     ┌────────────┐
       └───────────▶│  Redis   │     │  SICETAC   │
                    │ (Cache)  │     │ Webservice │
                    └──────────┘     └────────────┘
```

## 📦 Files Structure for Production

```
liftit-cotizador-sicetac/
├── docker-compose.prod.yml    # Production orchestration
├── Dockerfile.prod            # Optimized production image
├── .env.production           # Production environment variables
├── nginx/
│   └── conf.d/
│       └── sicetac.conf      # Nginx configuration
├── scripts/
│   ├── deploy.sh             # Deployment automation
│   ├── backup.sh             # Database backup script
│   └── init_db.sql           # PostgreSQL initialization
└── backups/                  # Backup directory
```

## 🔧 Step-by-Step Deployment

### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Clone and Configure

```bash
# Clone repository
git clone <repository-url> /opt/sicetac
cd /opt/sicetac

# Copy production environment file
cp .env.production .env

# Edit configuration
nano .env
```

### 3. Configure Environment Variables

Edit `.env` with your production values:

```env
# Critical Production Settings
DB_PASSWORD=<strong-password>
APP_SECRET_KEY=<generate-with-openssl-rand-hex-32>
SICETAC_PROD_USER=<your-sicetac-username>
SICETAC_PROD_PASS=<your-sicetac-password>
SENTRY_DSN=<your-sentry-dsn>  # Optional monitoring
```

### 4. SSL Certificate Setup

#### Option A: Let's Encrypt (Recommended)

```bash
# Run SSL setup
chmod +x scripts/deploy.sh
./scripts/deploy.sh production ssl
```

#### Option B: Manual Certificate

```bash
# Place certificates in nginx/ssl/
mkdir -p nginx/ssl
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/
chmod 600 nginx/ssl/*
```

### 5. Deploy Application

```bash
# Make deployment script executable
chmod +x scripts/deploy.sh

# Deploy to production
./scripts/deploy.sh production deploy
```

The script will:
- Check all requirements
- Create backups
- Build Docker images
- Start all services
- Run database migrations
- Perform health checks

### 6. Verify Deployment

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check API health
curl https://sicetac.liftit.com/api/healthz

# View logs
docker-compose -f docker-compose.prod.yml logs -f app

# Check database
docker exec sicetac-db psql -U sicetac_user -c "SELECT COUNT(*) FROM quotations;"
```

## 🔐 Security Configurations

### Firewall Setup

```bash
# Configure UFW firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Nginx Rate Limiting

Already configured in `nginx/conf.d/sicetac.conf`:
- API: 10 requests/second per IP
- Static: 30 requests/second per IP

### Database Security

- PostgreSQL runs in Docker network (not exposed)
- Strong passwords required
- SSL connections enforced in production
- Audit logging enabled

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# API health endpoint
curl https://sicetac.liftit.com/api/healthz

# Database health
docker exec sicetac-db pg_isready

# Redis health
docker exec sicetac-cache redis-cli ping
```

### Backup Strategy

Automatic daily backups configured:
```bash
# Manual backup
docker exec sicetac-backup /backup.sh

# List backups
ls -la backups/

# Restore from backup
gunzip < backups/sicetac_backup_YYYYMMDD.sql.gz | \
  docker exec -i sicetac-db psql -U sicetac_user sicetac_db
```

### Log Management

```bash
# Application logs
tail -f logs/app.log

# Nginx access logs
docker logs sicetac-nginx

# All service logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔄 Update Procedure

```bash
# Pull latest changes
git pull origin main

# Backup current deployment
./scripts/deploy.sh production backup

# Deploy update
./scripts/deploy.sh production deploy

# If issues occur, rollback
./scripts/deploy.sh production rollback
```

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check what's using port 80/443
sudo lsof -i :80
sudo lsof -i :443

# Stop conflicting service
sudo systemctl stop nginx  # If system nginx is running
```

**Database Connection Failed**
```bash
# Check PostgreSQL logs
docker logs sicetac-db

# Test connection
docker exec sicetac-db psql -U sicetac_user -d sicetac_db
```

**SSL Certificate Issues**
```bash
# Renew certificates
docker run -it --rm \
  -v $(pwd)/nginx/ssl:/etc/letsencrypt \
  certbot/certbot renew
```

**Out of Memory**
```bash
# Check memory usage
docker stats

# Adjust Docker memory limits in docker-compose.prod.yml
```

## 📈 Performance Optimization

### Recommended Server Specs

- **Minimum**: 2 CPU cores, 2GB RAM, 20GB SSD
- **Recommended**: 4 CPU cores, 4GB RAM, 40GB SSD
- **High Traffic**: 8 CPU cores, 8GB RAM, 100GB SSD

### Scaling Options

1. **Horizontal Scaling**: Add more app containers
```yaml
# In docker-compose.prod.yml
app:
  scale: 3  # Run 3 app instances
```

2. **Database Optimization**
- Add read replicas for heavy read loads
- Implement connection pooling
- Create appropriate indexes

3. **Caching Strategy**
- Redis caches SICETAC responses for 1 hour
- Static files cached for 30 days
- Database query results cached

## 🔑 Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | PostgreSQL password | `SecurePass123!` |
| `SICETAC_PROD_USER` | SICETAC username | `company_user` |
| `SICETAC_PROD_PASS` | SICETAC password | `api_password` |
| `SUPABASE_PROJECT_URL` | Supabase URL | `https://xyz.supabase.co` |
| `SENTRY_DSN` | Error tracking | `https://key@sentry.io/123` |
| `REDIS_URL` | Cache connection | `redis://localhost:6379/0` |

## 🆘 Support Contacts

- **Technical Issues**: devops@liftit.com
- **SICETAC Credentials**: Contact Ministry of Transport
- **Infrastructure**: cloud-team@liftit.com

## 📝 Post-Deployment Checklist

- [ ] SSL certificates installed and working
- [ ] Health check endpoint responding
- [ ] Database migrations completed
- [ ] Backup cron job running
- [ ] Monitoring alerts configured
- [ ] Documentation updated
- [ ] Team notified of deployment

## 🎉 Success Indicators

Your deployment is successful when:
- ✅ https://sicetac.liftit.com loads the interface
- ✅ API health check returns `{"status": "ok"}`
- ✅ Users can create quotations
- ✅ All Docker containers are healthy
- ✅ Logs show no critical errors

---

**Last Updated**: September 2024
**Platform Version**: 1.0.0
**Maintained by**: Liftit Engineering Team