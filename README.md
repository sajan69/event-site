# Event Site

## Overview

Event Site is a Django-based web application designed to manage and showcase events. It provides features for event creation, user authentication, ticket purchasing, and more. This README provides comprehensive instructions for both development and production processes.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Development Process](#development-process)
- [Production Process](#production-process)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Features

- User authentication (registration, login, logout)
- Event creation and management
- Ticket purchasing
- Admin panel for managing events and users
- Responsive design using Bootstrap
- Integration with payment gateways (Khalti, Stripe)
- QR code generation for event tickets

## Technologies Used

- Django Framework
- PostgreSQL Database (for production)
- SQLite Database (for development)
- Django Rest Framework (for API)
- Celery (for background tasks)
- Whitenoise (for serving static files)
- Cloudinary (for media file storage)
- HTML, CSS, JavaScript (for frontend)

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- PostgreSQL (for production)
- SQLite (for development)

### Clone the Repository

```bash
git clone https://github.com/sajan69/event-site.git
cd event-site
```

### Create a Virtual Environment

```bash
python -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Set Up Environment Variables

Create a `.env` file in the root directory and add the following variables:

```
SECRET_KEY=your_secret_key
DEBUG=True  # Set to False in production
DATABASE_URL=your_database_url  # For PostgreSQL
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
KHALTI_PUBLIC_KEY=your_khalti_public_key
KHALTI_SECRET_KEY=your_khalti_secret_key
STRIPE_PUBLIC_KEY=your_stripe_public_key
STRIPE_SECRET_KEY=your_stripe_secret_key
```

## Development Process

### Running the Development Server

To start the development server, run:

```bash
python manage.py runserver
```

You can access the application at `http://127.0.0.1:8000/`.

### Database Migrations

Run the following commands to set up the database:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collect Static Files

Before deploying, collect static files:

```bash
python manage.py collectstatic
```

### Creating a Superuser

To access the admin panel, create a superuser:

```bash
python manage.py createsuperuser
```

Follow the prompts to set up the superuser account.

## Production Process

### Deployment on Vercel

1. **Set Up Vercel Account**: Create an account on [Vercel](https://vercel.com/).

2. **Connect GitHub Repository**: Link your GitHub account and import the `event-site` repository.

3. **Configure Environment Variables**: In the Vercel dashboard, navigate to your project settings and add the environment variables defined in your `.env` file.

4. **Deploy**: Vercel will automatically build and deploy your application. Ensure that your `vercel.json` is correctly configured to handle static files and routes.

### Database Configuration

For production, ensure you have a PostgreSQL database set up. Update the `DATABASE_URL` in your environment variables to point to your PostgreSQL database.

## Usage

- Access the application at the deployed URL.
- Use the admin panel to manage events and users.
- Users can register, log in, and purchase tickets for events.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Make your changes and commit them (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.