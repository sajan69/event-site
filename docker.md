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

## Static Files Management

The project uses two directories for static files:
- `static/`: Used for development static files
- `staticfiles/`: Used for production static files (collected by collectstatic)

### Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

This command collects all static files from the `static/` directory and other installed apps into the `staticfiles/` directory, which is then served by Nginx in production.

### Adding New Static Files
1. For development, add static files to the `static/` directory
2. For production, run `collectstatic` to copy them to `staticfiles/`

## Media Files

Media files (user uploads) are stored in the `media/` directory and served by Nginx. Files uploaded through the application will be stored here.

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

## Troubleshooting

### Environment Variable Issues During Build
If you encounter errors related to missing environment variables during the Docker build process, ensure that:

1. Your `.env` file is properly formatted and contains all required variables
2. The `.env` file is mounted as a volume in your docker-compose.yml
3. Default values are provided in settings.py for critical environment variables

### Static Files Not Showing Up
If static files are not showing up in production:
1. Ensure collectstatic has run successfully
2. Check that the nginx configuration is pointing to the correct staticfiles directory
3. Verify permissions on the staticfiles directory
4. Check nginx logs for any errors

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
docker-compose exec web chmod -R 755 /app/static /app/staticfiles /app/media
```

## Scaling (For High Traffic)

### Scale Web Containers
```bash
docker-compose up -d --scale web=3
```

Note: When scaling, ensure your Nginx configuration is set up for load balancing.
```