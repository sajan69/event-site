## Docker Setup

This project is containerized using Docker for easy deployment and development.

### Prerequisites

- Docker
- Docker Compose

### Development Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/sajan69/event-site.git
   cd event-site
   ```

2. **Build and Start the Containers**:
   ```bash
   docker-compose up -d --build
   ```

3. **Access the Application**:
   Open your web browser and navigate to [http://localhost](http://localhost).

### Production Deployment

For production deployment, you should:

1. **Update the Nginx Configuration**:
   Modify the Nginx configuration file located at `nginx/conf.d/app.conf` to set your domain name.

2. **Set Up SSL Certificates**:
   Use Let's Encrypt or another SSL provider to secure your application.

3. **Update Environment Variables**:
   Ensure that your environment variables are set correctly for production.

Example production deployment:

```bash
# Set production environment variables
export FLASK_ENV=production
export SECRET_KEY=your-secure-secret-key

# Build and deploy
docker-compose -f docker-compose.yml up -d --build
```

### Container Management

- **Stop Containers**: 
  ```bash
  docker-compose down
  ```

- **View Logs**: 
  ```bash
  docker-compose logs -f
  ```

- **Access Shell in Web Container**: 
  ```bash
  docker-compose exec web bash
  ```

- **Access Database**: 
  ```bash
  docker-compose exec db psql -U postgres -d eventmaster
  ```

### Database Migrations

To run database migrations:   

```bash
docker-compose exec web python manage.py migrate
```

### Backup and Restore

To backup the database:

```bash
docker-compose exec db pg_dump -U postgres eventmaster > backup.sql
```

To restore from backup:

```bash
cat backup.sql | docker-compose exec -T db psql -U postgres eventmaster
```
```
