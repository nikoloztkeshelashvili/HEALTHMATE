# HealthMate

A simple web application for student health tracking with instructor management.

## Features

**Students:**
- Register with personal info and health goals
- Track daily weight
- View progress toward goal weight
- Calculate BMI and BMR automatically

**Instructors:**
- Register and login
- Add students by their ID
- View student progress
- Use BMI and BMR calculators

## Installation

1. Install requirements:
```bash
pip install flask flask-sqlalchemy
```

2. Run the app:
```bash
python app.py
```

3. Open browser to `http://localhost:5000`

## Usage

1. **Students:** Register, note your ID, then login with email and password
2. **Instructors:** Register, login, and add students using their ID
3. Both can use the calculators and track health data

Database is created automatically in `healthmate.db`