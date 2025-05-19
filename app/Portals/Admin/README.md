# CBS Admin Module

The CBS Admin Module is a Django-based administration panel for the CBS_PYTHON system. It functions as a central command center that enables administrators to control, configure, and monitor all modules and API-level functions.

## Architecture

This project follows Clean Architecture principles with the following layers:

1. **Domain Layer**: Core business entities and rules
2. **Application Layer**: Use cases and service interfaces
3. **Infrastructure Layer**: Implementation of repositories and services
4. **Presentation Layer**: Web views and API endpoints

## Features

- **Module Management**: Install, enable, disable, and configure system modules
- **API Management**: Configure, monitor, and control API endpoints
- **System Configuration**: Manage system-wide and module-specific configurations
- **System Monitoring**: Track system health, performance metrics, and status
- **User Management**: Manage admin users and their permissions
- **Audit Logging**: Track all administrative actions for accountability

## Setup and Installation

### Prerequisites

- Python 3.8+
- Django 4.0+
- Django REST Framework

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd CBS_PYTHON/Admin
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run setup script:
   ```
   python setup.py
   ```

4. Start the development server:
   ```
   python manage.py runserver
   ```

5. Access the admin panel:
   ```
   http://127.0.0.1:8000/
   ```

   Default credentials:
   - Username: admin
   - Password: Admin@123

   **Important:** Change the default password after first login!

## Project Structure

```
Admin/
├── cbs_admin/              # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── dashboard/              # Main app
│   ├── domain/             # Domain layer
│   │   └── entities/       # Domain entities
│   ├── application/        # Application layer
│   │   └── interfaces/     # Service and repository interfaces
│   ├── infrastructure/     # Infrastructure layer
│   │   ├── repositories/   # Repository implementations
│   │   └── services/       # Service implementations
│   ├── presentation/       # Presentation layer
│   │   ├── api/            # REST API
│   │   ├── views/          # Web views
│   │   └── templates/      # HTML templates
│   └── models.py           # Django models
├── requirements.txt        # Dependencies
└── setup.py                # Setup script
```

## Usage

### Module Management

The Module Management section allows you to:
- View all system modules
- Enable/disable modules
- View module dependencies
- Configure module-specific settings
- Monitor module health

### API Management

The API Management section allows you to:
- View all API endpoints
- Enable/disable endpoints
- Configure rate limiting
- View API metrics and usage statistics

### System Configuration

The System Configuration section allows you to:
- Configure system-wide settings
- Export and import configurations
- Manage environment-specific settings

### System Monitoring

The System Monitoring section provides:
- Real-time health metrics
- Historical performance data
- Resource usage trends
- Module-specific health information

### Audit Logs

The Audit Logs section shows:
- Administrative actions
- User activity
- System events
- Searchable and filterable logs

## Development

### Adding a New Module

To integrate a new module with the admin panel:

1. Create a module definition in the database
2. Register module's API endpoints
3. Define module-specific configurations
4. Implement health check functionality

### Extending the Admin Panel

To add new functionality to the admin panel:

1. Define any new entities in the domain layer
2. Create interfaces in the application layer
3. Implement services in the infrastructure layer
4. Add presentation components (API endpoints and web views)

## License

[Your License Information]

## Contributors

[List of Contributors]
