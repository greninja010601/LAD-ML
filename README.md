# Canvas LMS Dashboard Integration

This project provides a dashboard integration for Canvas Learning Management System using Django and LTI (Learning Tools Interoperability) protocol. The dashboard allows instructors to view and analyze student performance data.

## Features

- LTI integration with Canvas LMS
- Historical data storage using MySQL
- Instructor dashboard with analytics
- Secure communication through SSL

## Prerequisites

- **Python 3.x**
- **Django 4.1.1**: `pip install Django==4.1.1`
- **Canvas LMS Account**: Instructor-level access to a Canvas Instructure LMS instance
- **MySQL Server**: For storing historical data
- **mysqlclient**: For Django-MySQL connectivity
- **django-sslserver**: For secure local development

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://project.git
cd project
```

### 2. Set Up a Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Unix or MacOS
source venv/bin/activate
```

### 3. Install Required Dependencies

```bash
# Install Django and other dependencies
pip install -r requirements.txt

# If requirements.txt is not available, install these packages:
pip install Django==4.1.1
pip install mysqlclient
pip install django-sslserver
```

### 4. Database Configuration

#### MySQL Setup

1. Install MySQL Server on your machine if not already installed
2. Create a new database for the project
3. Configure Django to use MySQL by updating the `DATABASES` setting in `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'yourdbname',
        'USER': 'yourusername',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',  # Or an IP Address where your DB is hosted
        'PORT': '3306',
    }
}
```

4. Apply database migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Django Project Configuration

Update the following settings in `settings.py`:

1. Add required applications to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # Default Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    # ...
    # Project-specific apps
    'AppName',  # Replace with your actual app name
    'sslserver',
]
```

2. Disable CSRF for LTI functionality (Note: This is for development only, consider a more secure approach for production):

```python
# Comment out or remove the CSRF middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Commented out for LTI
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
```

3. Configure LTI settings:

```python
PYLTI_CONFIG = {
    'consumers': {
        '<random number string>': {
            'secret': '<random number string>'
        }
    }
}
```

### 6. Canvas LMS Configuration

1. Log in to your Canvas LMS instance with an instructor account
2. Navigate to the course where you want to add the dashboard
3. Go to "Settings" → "Apps" → "View App Configurations" → "+ App"
4. Select "By URL" or "Manual Entry" configuration type
5. Fill in the required details:
   - Name: Your Dashboard Name
   - Consumer Key: The same key used in your Django `PYLTI_CONFIG`
   - Shared Secret: The same secret used in your Django `PYLTI_CONFIG`
   - Launch URL: Your application's LTI launch URL (e.g., `https://127.0.0.1:8080/lti/`)
   - Select appropriate privacy settings

### 7. Canvas API Authorization

1. In your Canvas account, navigate to "Account" → "Settings" → "Approved Integrations" → "New Access Token"
2. Generate a new token (set an appropriate expiry date)
3. Copy this token and add it to your application's API configuration in `views.py`

### 8. Run the Development Server

For regular HTTP development server:

```bash
python manage.py runserver
```

For secure HTTPS development server (recommended for LTI):

```bash
python manage.py runsslserver localhost:<port_number>
```

## Usage

1. After configuring the LTI integration, the dashboard will appear as an external tool in your Canvas course
2. Launch the tool from your Canvas course to access the dashboard
3. The dashboard will authenticate via LTI and display relevant course data

## Troubleshooting

- If you encounter SSL certificate errors during development, make sure you're using `runsslserver` and have properly configured your browser to accept self-signed certificates
- For LTI authentication issues, verify that your consumer key and secret match between Canvas and your Django settings
- Database connection problems may require checking your MySQL server status and connection details

## License

[Your License Information]

## Contributing

[Your Contribution Guidelines]

## Contact

[Your Contact Information]
