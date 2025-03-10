# Docker Setup

This project is containerized using Docker for easy deployment and development in both local and production environments.

## Prerequisites

- Docker
- Docker Compose

## Local Development Setup

### 1. Clone the Repository
```bash
git clone https://github.com/sajan69/event-site.git
cd event-site
```

### 2. Create a .env File
Create a `.env` file in the project root with the necessary environment variables (see example in the repository).

### 3. Build and Start the Containers
```bash
docker-compose up -d --build
```

### 4. Run Migrations
```bash
docker-compose exec web python manage.py migrate
```

### 5. Create a Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Access the Application
Open your web browser and navigate to [http://localhost:8000](http://localhost:8000).

### 7. Access the Admin Panel
Open your web browser and navigate to [http://localhost:8000/admin](http://localhost:8000/admin).

## Production Deployment

### 1. Update Environment Variables
Modify the `.env` file with production settings:
```bash
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
SITE_URL=https://your-domain.com
```

### 2. Configure Nginx
Update the Nginx configuration in `nginx/conf.d/app.conf` with your domain name.

### 3. Set Up SSL Certificates
```bash
# Install certbot on your host machine
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificates
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### 4. Deploy with Docker Compose
```bash
docker-compose -f docker-compose.yml up -d --build
```

## Database Management

### Run Migrations
```bash
docker-compose exec web python manage.py migrate
```

### Create Database Backup
```bash
docker-compose exec db pg_dump -U postgres eventmaster > backup_$(date +%Y-%m-%d_%H-%M-%S).sql
```

### Restore from Backup
```bash
cat backup.sql | docker-compose exec -T db psql -U postgres eventmaster
```

## Seeding Data

### Seed All Data
```bash
docker-compose exec web python manage.py seed_db --all
```

### Seed Specific Data Types
```bash
docker-compose exec web python manage.py seed_db --categories --organizers --tags
```

### Clear and Seed Specific Data Types
```bash
docker-compose exec web python manage.py seed_db --clear-events --events
```

## Container Management

### View Running Containers
```bash
docker-compose ps
```

### Stop Containers
```bash
docker-compose down
```

### View Logs
```bash
docker-compose logs -f
```

### View Logs for a Specific Service
```bash
docker-compose logs -f web
```

### Access Shell in Web Container
```bash
docker-compose exec web bash
```

### Access Database CLI
```bash
docker-compose exec db psql -U postgres -d eventmaster
```

## Static and Media Files

### Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Media Files
Media files are stored in the `media` directory and served by Nginx. Files uploaded through the application will be stored here.

## Troubleshooting

### Environment Variable Issues During Build
If you encounter errors related to missing environment variables during the Docker build process, ensure that:

1. Your `.env` file is properly formatted and contains all required variables
2. The `.env` file is mounted as a volume in your docker-compose.yml
3. Default values are provided in settings.py for critical environment variables

Example error:

### Database Connection Issues
If you encounter database connection issues, ensure the database container is running:
```bash
docker-compose ps
```

If the database is not running, check the logs:
```bash
docker-compose logs db
```

### Migration Issues
If you encounter migration issues, try resetting the migrations:
```bash
docker-compose exec web python manage.py showmigrations
```

To apply a specific migration:
```bash
docker-compose exec web python manage.py migrate app_name migration_name
```

### Permissions Issues
If you encounter permissions issues with static or media files:
```bash
docker-compose exec web chmod -R 755 /app/static /app/media
```

## Scaling (For High Traffic)

### Scale Web Containers
```bash
docker-compose up -d --scale web=3
```

Note: When scaling, ensure your Nginx configuration is set up for load balancing.
```
