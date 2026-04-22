# Instagram Clone - Django Web Application

A full-stack Instagram-like web application built with Django and SQLite, featuring user authentication, posts, likes, comments, and follow system.

## Features

### Authentication System
- User registration with custom fields
- Login/logout functionality
- Custom user model with bio and profile picture

### User Profiles
- View and edit user profiles
- Display user posts
- Show followers and following counts
- Follow/unfollow users

### Posts
- Upload images with captions
- Display posts in chronological feed
- Delete own posts
- View individual post details

### Social Features
- Like/unlike posts with real-time updates
- Add and delete comments
- Follow system with relationship management

### User Interface
- Modern, Instagram-inspired design
- Responsive layout for mobile devices
- AJAX functionality for seamless interactions

## Project Structure

```
django-social-media/
├── manage.py
├── requirements.txt
├── README.md
├── instagram_clone/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── forms.py
├── posts/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── templatetags/
│       ├── __init__.py
│       └── post_extras.py
├── templates/
│   ├── base.html
│   ├── accounts/
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   ├── edit_profile.html
│   │   ├── followers_list.html
│   │   └── following_list.html
│   └── posts/
│       ├── feed.html
│       ├── create_post.html
│       ├── post_detail.html
│       ├── delete_post.html
│       └── user_posts.html
├── static/
└── media/
    ├── profile_pics/
    └── post_images/
```

## Installation and Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone or Download the Project
```bash
# If using git
git clone <repository-url>
cd django-social-media

# Or download and extract the project files
```

### Step 2: Create and Activate Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Database Setup
```bash
# Create and apply migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser for admin access
python manage.py createsuperuser
```

### Step 5: Create Media Directories
```bash
# Create directories for uploaded files
mkdir -p media/profile_pics
mkdir -p media/post_images

# Add a default profile picture (optional)
# Copy a default.jpg file to media/profile_pics/
```

### Step 6: Run the Development Server
```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

## Usage

### Getting Started
1. Navigate to `http://127.0.0.1:8000/accounts/register/` to create an account
2. Log in with your credentials
3. Complete your profile by adding a bio and profile picture
4. Start creating posts and following other users

### Main Features
- **Feed**: View posts from users you follow at `/feed/`
- **Create Post**: Upload images with captions at `/create/`
- **Profile**: View user profiles and posts at `/profile/<username>/`
- **Admin Panel**: Access Django admin at `/admin/` with superuser credentials

## Technology Stack

- **Backend**: Django 4.2.7
- **Database**: SQLite
- **Frontend**: Django Templates with Bootstrap 5
- **Image Processing**: Pillow
- **Forms**: django-crispy-forms with Bootstrap 5
- **Icons**: Bootstrap Icons
- **AJAX**: jQuery for dynamic interactions

## Configuration

### Settings
- Database configuration in `instagram_clone/settings.py`
- Media files configuration for uploads
- Static files configuration for CSS/JS
- Custom user model configuration

### Security Notes
- Change the `SECRET_KEY` in production
- Set `DEBUG = False` in production
- Configure proper `ALLOWED_HOSTS` for production
- Use environment variables for sensitive data

## API Endpoints

### Authentication
- `POST /accounts/register/` - User registration
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout

### Posts
- `GET /feed/` - Feed view
- `POST /create/` - Create new post
- `GET /post/<id>/` - Post detail view
- `DELETE /post/<id>/delete/` - Delete post
- `POST /post/<id>/like/` - Like/unlike post
- `POST /post/<id>/comment/` - Add comment
- `DELETE /comment/<id>/delete/` - Delete comment

### Users
- `GET /profile/<username>/` - User profile
- `POST /follow/<username>/` - Follow user
- `POST /unfollow/<username>/` - Unfollow user

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Feel free to use and modify as needed.

## Troubleshooting

### Common Issues

1. **Static files not loading**: Run `python manage.py collectstatic`
2. **Media uploads failing**: Check media directory permissions
3. **Database errors**: Ensure migrations are applied correctly
4. **Template not found**: Check template directory configuration

### Getting Help

- Check Django documentation: https://docs.djangoproject.com/
- Review error messages in the development server
- Use Django admin to verify data integrity

## Future Enhancements

- Real-time notifications
- Stories feature
- Direct messaging
- Hashtag support
- Post search functionality
- Image filters
- Video support
- Mobile app integration
