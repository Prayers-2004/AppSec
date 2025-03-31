# AppSec - Application Security System

AppSec is a comprehensive security solution that provides an extra layer of protection for applications by implementing multi-factor authentication and real-time intruder detection.

## Features

- User authentication system
- Application protection
- Intruder image capture
- Location tracking
- Real-time email alerts
- SAP HANA database integration

## Project Structure

```
appsec/
├── backend/           # Flask backend
│   ├── app/          # Application code
│   ├── config/       # Configuration files
│   └── tests/        # Backend tests
├── frontend/         # React frontend
│   ├── src/          # Source code
│   └── public/       # Static files
└── docs/            # Documentation
```

## Setup Instructions

### Backend Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the backend:
```bash
cd backend
flask run
```

### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Run the development server:
```bash
npm start
```

## Security Features

- Multi-factor authentication
- Intruder detection with image capture
- Location tracking
- Real-time email alerts
- Secure password storage
- JWT-based authentication

## Technologies Used

- Backend: Python Flask
- Frontend: React
- Database: SAP HANA
- Security: JWT, OpenCV
- Email: SMTP
- Location: Geopy

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. # AppSec
# AppSec
