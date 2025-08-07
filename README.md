# AI-Powered Fitness and Nutrition Planner Backend

A Django REST API backend that powers an intelligent fitness platform, providing personalized workout routines and nutrition plans through AI-driven recommendations.

## 🚀 Features

- **JWT Authentication** - Secure token-based user authentication system
- **User Profiles** - Extended user model with fitness goals and preferences
- **REST API** - Comprehensive endpoints for frontend integration
- **PostgreSQL Database** - Robust data storage solution

## 🛠️ Tech Stack

- **Django** - High-level Python web framework
- **Django REST Framework** - Powerful toolkit for building Web APIs
- **SimpleJWT** - JWT authentication for Django REST Framework
- **PostgreSQL** - Advanced open source database

## 📋 Prerequisites

- Python 3.9+
- PostgreSQL
- Virtual environment tool (venv, pipenv, or conda)

## ⚙️ Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/ai-powered-fitness-and-nutrition-planner-backend.git
cd ai-powered-fitness-and-nutrition-planner-backend
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

4. **Configure database**

Update settings.py with your PostgreSQL credentials or use environment variables.

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

The API uses JWT (JSON Web Tokens) for authentication:

```bash
# Register a new user
POST /api/auth/register/

# Login to get tokens
POST /api/auth/login/

# Refresh token
POST /api/auth/token/refresh/
```

Include the token in request headers:
```
Authorization: Bearer <your_access_token>
```

## 📚 API Endpoints

### User Management
- `GET /api/users/` - List all users (admin only)
- `GET /api/users/me/` - Get current user profile
- `PUT /api/users/update_profile/` - Update user profile

### Fitness Features
- `GET /api/workouts/` - List workout plans
- `POST /api/workouts/` - Create workout plan
- `GET /api/nutrition/` - List nutrition plans
- `POST /api/nutrition/` - Create nutrition plan

## 🧪 Testing

Run the test suite:

```bash
python manage.py test
```

## 🔄 Development Workflow

1. Create a new branch for your feature
2. Make changes and test locally
3. Run Django checks before committing:
   ```bash
   python manage.py check
   ```
4. Create a pull request

## 📝 Project Structure

```
ai-powered-fitness-and-nutrition-planner-backend/
├── api/                  # Main API project
├── rest/                 # Core app with models and views
├── fitness_planner/      # Project settings
├── venv/                 # Virtual environment
├── manage.py             # Django management script
└── requirements.txt      # Project dependencies
```

## 🚧 Future Development

- Workout tracking system
- Nutrition calculator
- Integration with fitness wearables
- Advanced AI recommendation engine
- Mobile app companion

## 👥 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Built with Django and ❤️ for fitness enthusiasts