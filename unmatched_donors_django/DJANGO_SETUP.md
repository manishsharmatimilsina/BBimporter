# Django Project Setup & Deployment Guide

## 📦 Project Structure

```
unmatched-donors-django/
├── config/                    # Django settings
│   ├── __init__.py
│   ├── settings.py           # Main settings
│   ├── urls.py               # Main URL config
│   ├── asgi.py               # ASGI config
│   ├── wsgi.py               # WSGI config
│   └── celery.py             # Celery config
├── analyzer/                 # Main Django app
│   ├── migrations/           # Database migrations
│   ├── models.py             # Data models
│   ├── views.py              # Views
│   ├── serializers.py        # DRF serializers
│   ├── tasks.py              # Celery tasks
│   ├── utils.py              # Utility functions
│   ├── urls.py               # App URLs
│   ├── admin.py              # Admin config
│   └── forms.py              # Forms
├── templates/                # HTML templates
│   ├── base.html
│   ├── analyzer/
│   │   ├── analysis_list.html
│   │   └── analysis_detail.html
├── static/                   # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── logs/                     # Log files
├── media/                    # Uploaded files
├── manage.py                 # Django management
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables
├── .gitignore                # Git ignore
├── Dockerfile                # Docker config
├── docker-compose.yml        # Docker compose
├── .github/
│   └── workflows/
│       ├── tests.yml         # Testing workflow
│       └── deploy.yml        # Deployment workflow
└── README.md                 # Project documentation
```

## 🚀 Local Development Setup

### 1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Database Migrations
```bash
python manage.py migrate
```

### 5. Create Superuser
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

### 7. Run Celery (in separate terminal)
```bash
celery -A config worker -l info
```

Visit: http://localhost:8000

## 🔧 Configuration

### Environment Variables (.env)
```
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=unmatched_donors
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Celery & Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3 (Optional)
USE_S3=False
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
```

## 🐳 Docker Setup

### Build & Run with Docker
```bash
# Build image
docker build -t unmatched-donors .

# Run container
docker run -p 8000:8000 unmatched-donors

# Or use docker-compose
docker-compose up -d
```

## 📝 API Endpoints

### Create Analysis Session
```bash
POST /api/analysis/
{
  "user": 1
}
```

### Upload File
```bash
POST /api/analysis/{id}/upload_file/
{
  "file_type": "benevity",
  "file": <file>
}
```

### Start Analysis
```bash
POST /api/analysis/{id}/analyze/
```

### Get Results
```bash
GET /api/analysis/{id}/results/
```

### Export CSV
```bash
GET /api/analysis/{id}/export_csv/
```

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Coverage
```bash
coverage run --source='.' manage.py test
coverage report
```

## 📋 Management Commands

### Create sample data
```bash
python manage.py create_sample_data
```

### Cleanup old files
```bash
python manage.py cleanup_old_files
```

## 🚀 Deployment

### Heroku
```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create unmatched-donors

# Set environment variables
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key

# Push to Heroku
git push heroku main
```

### AWS EC2
1. SSH into instance
2. Clone repository
3. Install Python and dependencies
4. Configure nginx/Apache
5. Set up SSL with Let's Encrypt
6. Configure Gunicorn

### DigitalOcean App Platform
1. Connect GitHub repository
2. Configure environment variables
3. Set up database
4. Deploy

## 📊 Admin Interface

Access at: `/admin`
- Manage analysis sessions
- View unmatched donors
- Monitor analysis logs

## 🔒 Security Checklist

- [ ] Set DEBUG = False in production
- [ ] Use strong SECRET_KEY
- [ ] Configure ALLOWED_HOSTS
- [ ] Enable HTTPS/SSL
- [ ] Use environment variables for secrets
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Enable authentication
- [ ] Use strong database passwords
- [ ] Backup database regularly

## 📈 Monitoring & Logging

- Django logs in `/logs/django.log`
- Celery logs separate
- Monitor Redis connection
- Check disk space for uploads

## 🛠️ Troubleshooting

### Database connection error
```bash
python manage.py dbshell  # Test connection
```

### Celery not working
```bash
celery -A config inspect active  # Check active tasks
```

### Static files not loading
```bash
python manage.py collectstatic --noinput
```

## 📚 Additional Resources

- Django Documentation: https://docs.djangoproject.com
- Django REST Framework: https://www.django-rest-framework.org
- Celery Documentation: https://docs.celeryproject.org
- PostgreSQL: https://www.postgresql.org/docs/

