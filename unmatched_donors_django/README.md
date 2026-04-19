# Unmatched Donors Analyzer - Django Web Application

[![Tests](https://github.com/yourusername/unmatched-donors-django/workflows/Tests/badge.svg)](https://github.com/yourusername/unmatched-donors-django/actions)
[![Deploy](https://github.com/yourusername/unmatched-donors-django/workflows/Deploy/badge.svg)](https://github.com/yourusername/unmatched-donors-django/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern Django web application for identifying unmatched donors across multiple donation platforms and exporting them in Blackbaud-compatible format.

## 🎯 Features

✅ **Web Interface**
- User-friendly dashboard for analysis
- Real-time file upload progress
- Interactive results visualization

✅ **Multiple Data Sources**
- BENEVITY RAW CSV
- FUP RAW CSV
- PAYPAL RAW CSV
- STRIPE RAW CSV
- GLOBALGIVING Excel
- Blackbaud Database CSV

✅ **Automated Processing**
- Asynchronous analysis with Celery
- Email-based donor deduplication
- Automatic filtering of failed donations
- "Fundraise Up" donation filtering

✅ **API & Integration**
- RESTful API for programmatic access
- Token-based authentication
- Webhooks for notifications
- CSV export in BB format

✅ **Production Ready**
- Docker containerization
- CI/CD pipelines
- Database migrations
- Comprehensive logging
- Error handling

## 🚀 Quick Start

### Using Docker (Recommended)
```bash
# Clone repository
git clone https://github.com/yourusername/unmatched-donors-django.git
cd unmatched-donors-django

# Start services
docker-compose up -d

# Access application
# Web: http://localhost:8000
# Admin: http://localhost:8000/admin
```

### Local Development
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# In another terminal, start Celery
celery -A config worker -l info
```

Visit: http://localhost:8000

## 📋 System Requirements

- **Python:** 3.9+
- **Database:** PostgreSQL 12+ (or SQLite for development)
- **Redis:** 6.0+ (for Celery)
- **Docker:** 20.10+ (optional, for containerization)

## 🔧 Configuration

### Environment Variables
See `.env.example` for all available options:

```bash
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=unmatched_donors
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# AWS S3 (Optional)
USE_S3=False
AWS_STORAGE_BUCKET_NAME=your-bucket
AWS_S3_REGION_NAME=us-east-1
```

## 📚 API Documentation

### Authentication
```bash
# Get token
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Use token in requests
curl -H "Authorization: Token YOUR_TOKEN" http://localhost:8000/api/analysis/
```

### Create Analysis Session
```bash
POST /api/analysis/
Content-Type: application/json

{}

Response:
{
  "id": 1,
  "session_id": "abc123def456",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Upload Files
```bash
POST /api/analysis/{id}/upload_file/
Content-Type: multipart/form-data

Parameters:
- file_type: benevity | fup | paypal | stripe | globalgiving | bb
- file: <file>
```

### Start Analysis
```bash
POST /api/analysis/{id}/analyze/

Response:
{
  "message": "Analysis started",
  "session_id": "abc123def456"
}
```

### Get Results
```bash
GET /api/analysis/{id}/results/

Response:
{
  "status": "completed",
  "summary": {
    "total_donors": 1367,
    "unique_donors": 1143,
    "unmatched_donors": 653,
    "matched_donors": 490,
    "match_rate": 42.9
  },
  "source_breakdown": {
    "fup": 472,
    "paypal": 181,
    "stripe": 0
  },
  "donors": [...]
}
```

### Export CSV
```bash
GET /api/analysis/{id}/export_csv/

Returns: CSV file in Blackbaud import format
```

## 🧪 Testing

### Run Tests
```bash
python manage.py test

# Or with pytest
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Test Coverage
```bash
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

## 📊 Admin Interface

Access at: `/admin`

**Features:**
- Manage users and permissions
- View analysis sessions
- Browse unmatched donors
- Check analysis logs
- Monitor system health

## 🚢 Deployment

### Heroku
```bash
heroku create unmatched-donors
git push heroku main
heroku run python manage.py migrate
```

### AWS
See `DJANGO_SETUP.md` for detailed AWS EC2 deployment instructions.

### DigitalOcean
```bash
# In DigitalOcean App Platform
1. Connect GitHub repository
2. Configure environment variables
3. Set up managed database
4. Deploy
```

### Docker
```bash
# Build
docker build -t unmatched-donors .

# Run
docker run -p 8000:8000 \
  -e DEBUG=False \
  -e SECRET_KEY=your-key \
  unmatched-donors
```

## 📈 Monitoring

### Logs
```bash
# Django logs
tail -f logs/django.log

# Celery logs (Docker)
docker-compose logs celery

# Check task status
celery -A config inspect active
```

### Health Checks
```bash
# API health
curl http://localhost:8000/api/health/

# Database
python manage.py dbshell

# Redis
redis-cli ping
```

## 🔒 Security

### Checklist
- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS/SSL
- [ ] Set up firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable CORS appropriately
- [ ] Implement rate limiting
- [ ] Regular security audits
- [ ] Keep dependencies updated

## 📦 Project Structure

```
unmatched-donors-django/
├── config/                 # Django configuration
│   ├── settings.py        # Settings
│   ├── urls.py            # URL configuration
│   ├── wsgi.py            # WSGI
│   ├── asgi.py            # ASGI
│   └── celery.py          # Celery config
├── analyzer/              # Main application
│   ├── models.py          # Database models
│   ├── views.py           # Views
│   ├── serializers.py     # DRF serializers
│   ├── tasks.py           # Celery tasks
│   ├── utils.py           # Utilities
│   └── admin.py           # Admin config
├── templates/             # HTML templates
├── static/                # CSS, JS, images
├── tests/                 # Test files
├── .github/               # GitHub Actions
├── Dockerfile             # Docker config
├── docker-compose.yml     # Docker Compose
├── requirements.txt       # Python dependencies
└── manage.py              # Django management
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📖 Documentation

- [Setup Guide](DJANGO_SETUP.md)
- [API Documentation](docs/api.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guide](CONTRIBUTING.md)

## 🆘 Troubleshooting

### Database connection error
```bash
python manage.py dbshell
```

### Static files not loading
```bash
python manage.py collectstatic --noinput
```

### Celery not processing tasks
```bash
celery -A config inspect active
```

### Port already in use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - Initial work - [GitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Django Community
- Django REST Framework
- Celery Team
- All Contributors

## 📞 Support

For support, email support@example.com or create an issue on GitHub.

## 🗺️ Roadmap

- [ ] Mobile app (React Native)
- [ ] Advanced analytics dashboard
- [ ] Machine learning for donor matching
- [ ] Multi-language support
- [ ] Custom field mapping
- [ ] Webhook notifications
- [ ] Rate limiting enhancements

---

**[Visit Website](https://example.com)** | **[Documentation](docs/)** | **[Issues](https://github.com/yourusername/unmatched-donors-django/issues)**
