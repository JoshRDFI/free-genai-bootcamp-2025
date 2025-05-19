# Language Learning Portal

A web-based portal for managing your Japanese language learning journey. This application provides a central interface to track your progress, manage vocabulary, and integrate with other learning tools.

## Components

- **Frontend**: React-based web interface
- **Backend**: FastAPI-based REST API
- **Database**: SQLite database for user data and progress tracking

## Requirements

- Python 3.10 or higher
- Node.js and npm
- WSL2 (if running on Windows)

## Setup

The setup process is automated through the main project's setup script. It will:

1. Create a Python virtual environment
2. Install Python dependencies
3. Install Node.js dependencies
4. Set up the database
5. Configure the development environment

## Development

To start the development server:

```bash
./start_portal.py
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

## Architecture

- Frontend: React + TypeScript
- Backend: FastAPI + SQLAlchemy
- Authentication: JWT-based
- Database: SQLite with async support
