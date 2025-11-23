# Django Ticketing System

A comprehensive ticketing system built with Django for managing automation requests and support tickets.

## Features

### Core Functionality
- **User Management**: Role-based authentication (Admin, Automation Team, General Users)
- **Ticket Lifecycle**: Complete ticket management from creation to closure
- **Real-time Notifications**: Email and on-screen notifications for ticket events
- **Analytics Dashboard**: Comprehensive analytics and reporting
- **Mobile Responsive**: Fully responsive Bootstrap 5 interface

### User Roles
- **General Users**: Create tickets, view own tickets, add comments
- **Automation Team**: View assigned tickets, update status, manage assignments
- **Administrators**: Full system access, user management, analytics

### Ticket Features
- Custom categories (Automation, Bug Reports, Feature Requests, etc.)
- Priority levels (Low, Medium, High, Urgent)
- Status tracking (Open, In Progress, Delivered, Closed)
- Comment system with public/internal notes
- File attachments support
- Status history tracking
- Due date management

## Technology Stack

- **Backend**: Django 4.2+ with Python 3.11+
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Django Templates with Bootstrap 5
- **Task Queue**: Celery with Redis
- **Email**: SMTP email notifications
- **Security**: CSRF protection, XSS prevention, secure sessions

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis server
- Node.js (for development tools)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd TicketingApp2/backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Setup database**
   ```bash
   # Create database in PostgreSQL
   createdb ticketing_system

   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

8. **Start Celery worker** (in separate terminal)
   ```bash
   celery -A ticketing_system worker --loglevel=info
   ```

9. **Start Celery beat** (in separate terminal)
   ```bash
   celery -A ticketing_system beat --loglevel=info
   ```

10. **Run development server**
    ```bash
    python manage.py runserver
    ```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DB_NAME=ticketing_system
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost

# Email (for notifications)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Redis
REDIS_URL=redis://localhost:6379/0
```

## Usage

### Initial Setup

1. **Create Admin User**
   - Run `python manage.py createsuperuser`
   - This will be your first administrator account

2. **Add Team Members**
   - Log in as admin
   - Go to Django Admin (/admin/)
   - Add users with appropriate roles (automation_team, admin)

3. **Configure Email**
   - Set up SMTP credentials in .env
   - Test email functionality by creating a test ticket

### Daily Operations

#### For General Users:
1. Log in with your credentials
2. Create new tickets from the dashboard
3. Track ticket status in "My Tickets"
4. Add comments to communicate with the team

#### For Automation Team:
1. View assigned tickets on your dashboard
2. Update ticket status as work progresses
3. Add internal notes for team communication
4. Assign tickets to appropriate team members

#### For Administrators:
1. Monitor system health in analytics dashboard
2. Manage user accounts and roles
3. Generate performance reports
4. Configure system settings

## API Endpoints

### Ticket Management
- `GET /tickets/` - List tickets (filtered by user role)
- `POST /tickets/create/` - Create new ticket
- `GET /tickets/<id>/` - View ticket details
- `POST /tickets/<id>/assign/` - Assign ticket
- `POST /tickets/<id>/status/` - Update status
- `POST /tickets/<id>/comment/` - Add comment

### User Management
- `GET /users/login/` - User login
- `POST /users/register/` - User registration
- `GET /users/profile/` - View profile
- `POST /users/profile/edit/` - Update profile

### Notifications
- `GET /notifications/unread/` - Get unread count
- `GET /notifications/list/` - Get notification list
- `POST /notifications/mark-read/<id>/` - Mark as read

## Database Schema

### Core Tables
- **users**: Custom user model with roles and profile information
- **tickets**: Main ticket records with status, priority, and metadata
- **comments**: Ticket comments and communication
- **ticket_status_history**: Status change tracking
- **notifications**: User notifications for system events

### Key Relationships
- Users can create multiple tickets (one-to-many)
- Tickets can be assigned to users (many-to-one)
- Tickets can have multiple comments (one-to-many)
- Users can receive multiple notifications (one-to-many)

## Security Features

- **Authentication**: Secure password handling with Django's built-in auth
- **Authorization**: Role-based access control with custom mixins
- **CSRF Protection**: All forms protected with CSRF tokens
- **XSS Prevention**: Auto-escaping in templates, content sanitization
- **Session Security**: Secure session configuration with timeouts
- **Input Validation**: Form validation and model field constraints
- **File Upload Security**: File type and size restrictions

## Performance Optimizations

- **Database Indexing**: Optimized queries for ticket filters
- **Query Optimization**: Efficient database queries with select_related/prefetch_related
- **Caching**: Redis for session and task queue storage
- **Static Files**: Optimized CSS/JS with production deployment
- **Background Tasks**: Async email sending with Celery

## Testing

### Run Tests
```bash
python manage.py test
```

### Test Coverage
```bash
coverage run --source='.' manage.py test
coverage report
```

## Deployment

### Production Setup

1. **Web Server**: Gunicorn + Nginx
2. **Database**: PostgreSQL with connection pooling
3. **Cache**: Redis for sessions and Celery
4. **Static Files**: Nginx serving static files
5. **SSL**: Let's Encrypt certificates
6. **Monitoring**: Error logging and health checks

### Environment Settings
Set `DEBUG=False` and configure production security settings:
```bash
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request

## Support

For issues and questions:
1. Check the documentation
2. Search existing issues
3. Create a new issue with detailed information
4. Contact the development team

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### Version 1.0.0
- Initial release
- Core ticketing functionality
- User management system
- Email notifications
- Analytics dashboard
- Mobile responsive design