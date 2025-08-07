# FitPal Backend

An AI-powered fitness and nutrition planner backend built with Django REST Framework. FitPal provides personalized workout routines and nutrition plans through intelligent AI-driven recommendations using Google's Generative AI.

## 🚀 Features

- **AI-Powered Plans** - Generate personalized fitness and nutrition plans using Google Generative AI
- **Social Authentication** - Google OAuth2 integration with django-allauth
- **JWT Authentication** - Secure token-based authentication with dj-rest-auth
- **User Profiles** - Extended user model with fitness goals and preferences
- **REST API** - Comprehensive endpoints for frontend integration
- **SQLite Database** - Lightweight development database (configurable for production)

## 🛠️ Tech Stack

- **Django** - High-level Python web framework
- **Django REST Framework** - Powerful toolkit for building Web APIs
- **dj-rest-auth** - Authentication endpoints for DRF
- **django-allauth** - Social authentication (Google OAuth2)
- **Google Generative AI** - AI-powered plan generation
- **PyJWT** - JSON Web Token implementation
- **SQLite/PostgreSQL** - Database options

## 📋 Prerequisites

- Python 3.9+
- Virtual environment tool (venv, pipenv, or conda)
- Google AI API key (for Generative AI features)

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/hcissey0/fitpal-backend.git
cd fitpal-backend
```

2. **Set up virtual environment**

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Environment Configuration**

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
GOOGLE_AI_API_KEY=your-google-ai-api-key
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
```

5. **Run migrations**

```bash
python manage.py migrate
```

6. **Create superuser**

```bash
python manage.py createsuperuser
```

7. **Start development server**

```bash
python manage.py runserver
```

## 🔑 API Authentication

The API supports multiple authentication methods:

### JWT Authentication
```bash
# Register a new user
POST /api/auth/register/

# Login to get tokens
POST /api/auth/login/

# Refresh token
POST /api/auth/token/refresh/
```

### Social Authentication
```bash
# Google OAuth2 login
POST /api/auth/google/

# List social accounts
GET /api/auth/socialaccounts/

# Disconnect social account
POST /api/auth/socialaccounts/{id}/disconnect/
```

Include the token in request headers:
```
Authorization: Bearer <your_access_token>
```

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/token/refresh/` - Refresh JWT token
- `POST /api/auth/google/` - Google OAuth2 login

### User Management
- `GET /api/users/me/` - Get current user profile
- `PUT /api/users/update_profile/` - Update user profile

### AI-Powered Features
- `POST /api/generate-plan/` - Generate personalized fitness/nutrition plan
- `GET /api/plans/` - List user's saved plans
- `GET /api/plans/{id}/` - Get specific plan details

## 🧪 Testing

Run the test suite:

```bash
python manage.py test
```

Run Django system checks:

```bash
python manage.py check
```

## 📁 Project Structure

```
fitpal-backend/
├── api/                  # Main API configuration
│   ├── settings.py       # Django settings
│   ├── urls.py          # URL routing
│   └── wsgi.py          # WSGI configuration
├── rest/                 # Core REST API app
│   ├── models.py        # Data models
│   ├── views.py         # API views
│   ├── serializers.py   # DRF serializers
│   ├── urls.py          # App URLs
│   └── ai_service.py    # AI integration service
├── venv/                # Virtual environment
├── .env                 # Environment variables
├── .gitignore          # Git ignore rules
├── db.sqlite3          # SQLite database
├── manage.py           # Django management script
└── requirements.txt    # Project dependencies
```

## 🤖 AI Service

The AI service (`rest/ai_service.py`) integrates with Google's Generative AI to create personalized fitness and nutrition plans based on:

- User fitness goals
- Current fitness level
- Dietary preferences and restrictions
- Available equipment
- Time constraints

## 🔧 Configuration

### Database Configuration
The project uses SQLite by default for development. For production, configure PostgreSQL in `settings.py`.

### Google AI Setup
1. Get a Google AI API key from Google AI Studio
2. Add the API key to your `.env` file
3. Configure the AI service in `ai_service.py`

### Social Authentication Setup
1. Create a Google OAuth2 application
2. Configure redirect URIs
3. Add client ID and secret to `.env` file

## 🚀 Deployment

### Environment Variables for Production
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=your-database-url
GOOGLE_AI_API_KEY=your-google-ai-api-key
```

### Database Migration for Production
```bash
python manage.py collectstatic
python manage.py migrate
```

## 🧪 Development

### Adding New Features
1. Create models in `rest/models.py`
2. Create serializers in `rest/serializers.py`
3. Create views in `rest/views.py`
4. Add URL patterns in `rest/urls.py`
5. Run migrations: `python manage.py makemigrations && python manage.py migrate`

### Code Style
Follow Django best practices and PEP 8 styling guidelines.

## 🚧 Future Enhancements

- [ ] Workout progress tracking
- [ ] Nutrition logging and analysis
- [ ] Integration with fitness wearables
- [ ] Advanced AI recommendation algorithms
- [ ] Real-time chat support
- [ ] Mobile push notifications
- [ ] Social features and community

## 👥 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**FitPal** - Your AI-powered fitness companion 💪🤖