# GitHub & Deployment Guide

## 🚀 GitHub Setup

### 1. Create GitHub Repository

```bash
# Navigate to your project directory
cd /path/to/unmatched-donors-django

# Initialize git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: Django unmatched donors analyzer"

# Add remote (replace with your repository URL)
git remote add origin https://github.com/yourusername/unmatched-donors-django.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to `Settings → Secrets and variables → Actions` and add:

```
DOCKER_USERNAME        - Your Docker Hub username
DOCKER_PASSWORD        - Your Docker Hub password/token
SERVER_HOST            - Your server IP/domain
SERVER_USER            - SSH user for server
SERVER_SSH_KEY         - Private SSH key for deployment
SLACK_WEBHOOK          - Slack webhook for notifications (optional)
```

### 3. GitHub Actions Setup

Workflows are in `.github/workflows/`:
- `tests.yml` - Runs tests on every push/PR
- `deploy.yml` - Deploys on main branch push

## 🐳 Deployment Options

### Option 1: Heroku (Easiest)

#### Prerequisites
```bash
# Install Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

heroku login
```

#### Deploy
```bash
# Create Heroku app
heroku create unmatched-donors

# Set environment variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
heroku config:set ALLOWED_HOSTS=unmatched-donors.herokuapp.com

# Add PostgreSQL
heroku addons:create heroku-postgresql:essential-0

# Add Redis
heroku addons:create heroku-redis:premium-0

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Create superuser
heroku run python manage.py createsuperuser
```

Visit: `https://unmatched-donors.herokuapp.com`

### Option 2: DigitalOcean App Platform

#### Setup via DigitalOcean Dashboard
1. Click "Apps" → "Create App"
2. Connect GitHub repository
3. Select `unmatched-donors-django`
4. Configure environment variables
5. Create managed PostgreSQL database
6. Create managed Redis instance
7. Deploy

#### Configuration
```yaml
name: unmatched-donors
services:
  - name: web
    dockerfile_path: Dockerfile
    source_dir: /
    http_port: 8000
    envs:
      - key: DEBUG
        value: "False"
      - key: SECRET_KEY
        value: ${SECRET_KEY}
      - key: DATABASE_URL
        scope: RUN_AND_BUILD_TIME
        value: ${db.connection_string}
      - key: CELERY_BROKER_URL
        value: redis://${cache.hostname}:${cache.port}
    http_routes:
      - path: /
        preserve_path_prefix: true

databases:
  - name: db
    engine: PG
    version: "15"
    
  - name: cache
    engine: REDIS
    version: "7"
```

### Option 3: AWS EC2

#### Step 1: Launch EC2 Instance
```bash
# Connect to instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Update system
sudo yum update -y
sudo yum install -y python3 python3-pip postgresql-client git nginx

# Install Docker
sudo yum install -y docker
sudo systemctl start docker
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Step 2: Clone Repository
```bash
cd /app
git clone https://github.com/yourusername/unmatched-donors-django.git
cd unmatched-donors-django
```

#### Step 3: Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your values
```

#### Step 4: Start Services
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

#### Step 5: Setup Nginx
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /app/unmatched-donors-django/staticfiles/;
    }

    location /media/ {
        alias /app/unmatched-donors-django/media/;
    }
}
```

#### Step 6: SSL with Let's Encrypt
```bash
sudo yum install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Option 4: Google Cloud Run

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project your-project-id

# Build and deploy
gcloud run deploy unmatched-donors \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars DEBUG=False,SECRET_KEY=your-key,DATABASE_URL=your-db-url
```

### Option 5: Azure App Service

```bash
# Create resource group
az group create --name unmatched-donors --location eastus

# Create App Service plan
az appservice plan create \
    --name unmatched-donors-plan \
    --resource-group unmatched-donors \
    --sku B1 --is-linux

# Create web app
az webapp create \
    --resource-group unmatched-donors \
    --plan unmatched-donors-plan \
    --name unmatched-donors \
    --runtime "PYTHON|3.11"

# Configure deployment from GitHub
az webapp deployment source config \
    --resource-group unmatched-donors \
    --name unmatched-donors \
    --repo-url https://github.com/yourusername/unmatched-donors-django \
    --branch main \
    --manual-integration
```

## 📊 Post-Deployment

### 1. Verify Installation
```bash
# Check if services are running
docker-compose ps

# Check logs
docker-compose logs web
docker-compose logs celery

# Test API
curl -X GET http://localhost:8000/api/health/
```

### 2. Create Admin User
```bash
docker-compose exec web python manage.py createsuperuser
```

### 3. Load Sample Data (optional)
```bash
docker-compose exec web python manage.py loaddata samples/sample_data.json
```

### 4. Setup Backups
```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)

docker-compose exec -T db pg_dump -U postgres unmatched_donors > \
    $BACKUP_DIR/backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

## 🔒 Security Hardening

### 1. Firewall Rules
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw default deny incoming
sudo ufw enable
```

### 2. SSL Certificate
```bash
# Let's Encrypt (automatic renewal)
sudo certbot renew --dry-run
```

### 3. Regular Updates
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Update Docker images
docker-compose pull
docker-compose up -d

# Update system
sudo apt update && sudo apt upgrade -y
```

### 4. Database Backups
```bash
# Automated daily backups
0 2 * * * /usr/local/bin/backup.sh
```

## 📈 Monitoring & Logging

### Application Logs
```bash
# View logs
docker-compose logs -f web

# Celery logs
docker-compose logs -f celery

# All logs
docker-compose logs -f
```

### System Monitoring
```bash
# CPU/Memory
docker stats

# Disk space
df -h
```

### Health Checks
```bash
# API health
curl http://localhost:8000/api/health/

# Database
docker-compose exec web python manage.py dbshell

# Redis
redis-cli ping
```

## 🛠️ Maintenance

### Database Cleanup
```bash
# Remove old uploaded files
docker-compose exec web python manage.py cleanup_old_files

# Optimize database
docker-compose exec web python manage.py optimize_db
```

### Update Django
```bash
# Update Django and dependencies
pip install --upgrade Django
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push origin main
```

## 🆘 Troubleshooting

### Application won't start
```bash
# Check logs
docker-compose logs web

# Check migrations
docker-compose exec web python manage.py migrate --check

# Run migrations
docker-compose exec web python manage.py migrate
```

### Database connection error
```bash
# Test connection
docker-compose exec web python manage.py dbshell

# Restart database
docker-compose restart db
```

### Celery tasks not processing
```bash
# Check Celery status
celery -A config inspect active

# Restart Celery
docker-compose restart celery
```

### Out of disk space
```bash
# Check disk usage
docker system df

# Clean up Docker
docker system prune
docker image prune
```

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/deployment/checklist/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Heroku Documentation](https://devcenter.heroku.com)
- [DigitalOcean Docs](https://docs.digitalocean.com)

## 🎯 Next Steps

1. ✅ Create GitHub repository
2. ✅ Configure GitHub Secrets
3. ✅ Choose deployment platform
4. ✅ Deploy application
5. ✅ Setup monitoring
6. ✅ Configure backups
7. ✅ Document procedures

---

**Questions?** Check the troubleshooting section or open an issue on GitHub.
