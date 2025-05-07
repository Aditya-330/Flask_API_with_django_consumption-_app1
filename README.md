# Django-healthcare-booking-pharmacy-

# CureClick

CureClick is a comprehensive healthcare platform that combines an online pharmacy service with doctor consultation booking. The application enables users to purchase medicines, book appointments with healthcare professionals, and manage their healthcare needs in one place.

## Features

### Online Pharmacy
- Browse and purchase medicines
- Search functionality for finding medications
- Shopping cart system
- Prescription uploads for prescription-only medicines
- Order tracking system
- Promo code support for discounts

### Doctor Consultation
- Doctor appointment booking system
- Consultation type selection
- Time slot availability management
- Appointment rescheduling
- Appointment status tracking
- Doctor dashboard for healthcare providers

### User Management
- User registration and authentication
- User profiles with health information
- Order history
- Appointment history
- Secure payment processing

## Technology Stack

- **Backend**: Django 5.2
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: SQLite (development)
- **Additional Packages**:
  - django-crispy-forms
  - crispy-bootstrap5
  - Pillow (for image processing)
  - django-rest-framework (for API endpoints)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/CureClick.git
   cd CureClick
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv myenv
   myenv\Scripts\activate

   # Linux/Mac
   python -m venv myenv
   source myenv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   ```

5. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

8. Access the application at `http://localhost:8000`

## Project Structure

```
CureClick/
├── WebDevProject/
│   ├── CureClick/
│   │   ├── FLtoDjango/          # Doctor consultation app
│   │   ├── pharmacy/           # Online pharmacy app
│   │   ├── media/             # User-uploaded files
│   │   ├── static/            # Static files
│   │   └── templates/         # HTML templates
│   └── manage.py
├── requirements.txt
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout

### Pharmacy
- `GET /api/medicines/` - List all medicines
- `GET /api/medicines/{id}/` - Get medicine details
- `POST /api/orders/` - Create new order
- `GET /api/orders/` - List user orders

### Doctor Consultation
- `GET /api/doctors/` - List all doctors
- `GET /api/doctors/{id}/` - Get doctor details
- `POST /api/appointments/` - Book appointment
- `GET /api/appointments/` - List user appointments

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributors

- [Aditya]
- [Dhruv Mahajan]
- [Neelabh]
- [Saksham Sheoran]

## Acknowledgments

- Special thanks to all contributors and users of the CureClick platform
- Thanks to the Django community for their excellent documentation and support
