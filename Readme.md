# Gym Training Optimizer System

A complete Django web application for selecting the optimal load for training in the gym, tracking progress, and managing nutrition.

## Features

- User registration and authentication (including Google OAuth)
- User profile management (gender, height, weight, age, fitness level, injuries)
- Personalized workout generation based on user goals
- Progress tracking (weight, muscle mass, body fat percentage)
- Workout scheduling and editing
- Automatic load adjustment based on progress
- Nutrition recommendations and meal planning
- Integration with Google Fit / Apple HealthKit
- Workout reminders via SMS (Twilio API)
- Interactive charts and analytics
- AI-powered workout and meal plan generation (OpenAI API)

## Tech Stack

- Django (ORM, Django REST Framework)
- SQLite (database, can be switched to PostgreSQL)
- Celery + Redis (asynchronous task queue)
- Django Templates + Bootstrap (UI)
- Google OAuth API (authentication)
- Spoonacular API (nutrition recommendations)
- Twilio API (SMS notifications)
- Chart.js (interactive charts)

## Project Structure

- **gym_optimizer/**: Main project directory
- **users/**: User account management and profiles
- **workouts/**: Workout plans, exercises, and scheduling
- **progress/**: Progress tracking and analytics
- **nutrition/**: Meal planning and nutrition tracking
- **api/**: REST API endpoints

## Installation Instructions

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Redis (for Celery)

### Step 1: Clone the repository

```bash
git clone https://github.com/Ammuseku/gym_project.git
cd gym_project
```

### Step 2: Create and activate virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Unix/macOS
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create environment variables file

Create a `.env` file in the project root directory with the following variables:

```
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Twilio
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number

# Spoonacular
SPOONACULAR_API_KEY=your_spoonacular_api_key

### Step 5: Run migrations and create a superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```


### Step 5: Run the development server

```bash
python manage.py runserver
```

Access the application at http://127.0.0.1:8000/

## Initial Setup After Installation

1. Log in to the admin interface at http://127.0.0.1:8000/admin/
2. Add muscle groups and exercises
3. Create sample workout plans and meal plans

## API Documentation

The REST API is available at http://127.0.0.1:8000/api/

Authentication is required for most endpoints and can be handled via:
- Session authentication (for web browser access)
- Token authentication (for mobile apps or external services)

## External API Setup

### Google OAuth

1. Create a project in Google Cloud Console
2. Enable the Google+ API and Google Fit API
3. Configure OAuth consent screen
4. Create OAuth 2.0 Client ID credentials
5. Add authorized redirect URIs: `http://localhost:8000/accounts/google/login/callback/`

### Spoonacular API

1. Register for a Spoonacular API key at https://spoonacular.com/food-api
2. Add the API key to your `.env` file


### Twilio API

1. Register for a Twilio account at https://www.twilio.com/
2. Get your Account SID, Auth Token, and phone number
3. Add these details to your `.env` file

## Deployment Instructions

For production deployment, the following changes are recommended:

1. Set `DEBUG=False` in `.env`
2. Use PostgreSQL instead of SQLite
3. Configure a production-ready web server like Nginx with Gunicorn
4. Enable HTTPS with Let's Encrypt
5. Configure email settings for production
6. Set up proper logging

## License

MIT License

## Contributors

- Your Name <muslimovamir42@gmail.com>
