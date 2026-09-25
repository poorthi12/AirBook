# AirBook

AirBook is a Flask-based flight booking web application for searching flights, booking tickets, managing passenger details, and handling user authentication.

Link To Access AirBook  : https://airbookofficial.vercel.app/

## Features

- User registration and login
- Email OTP verification during signup
- Search flights by city and date
- View flight details and available seats
- Book flights with passenger information
- Payment and booking review flow
- Admin dashboard for booking and flight management
- MongoDB-backed data storage

## Tech Stack

- Python 3
- Flask
- MongoDB / PyMongo (Used MongoDB Atlas for Cloud Database service)
- Flask-Mail for OTP email delivery
- ReportLab and qrcode for PDF / QR features
- Jinja2 templates and custom CSS/JS

## Project Structure

- `app.py` - main Flask application
- `config.py` - configuration and environment variable parsing
- `database/` - MongoDB connection and seed scripts
- `routes/` - app route blueprints
- `templates/` - HTML pages
- `static/` - CSS, JS, and images
- `utils/` - helper utilities
- `tests/` - project tests

## Prerequisites

Before running the app, make sure you have:

- Python 3.10+
- A MongoDB instance or MongoDB Atlas connection string
- An SMTP-capable email provider for OTP emails (Gmail or another SMTP server)

## Setup

1. Clone the project and open the folder:

   ```bash
   git clone <your-repo-url>
   cd AirBook
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root based on the sample below:

   ```env
   MONGO_URI=mongodb+srv://<username>:<password>@<cluster-url>/<database-name>?retryWrites=true&w=majority
   SECRET_KEY=your-super-secret-key

   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=465
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   MAIL_DEFAULT_SENDER=your-email@gmail.com
   MAIL_USE_SSL=true
   MAIL_USE_TLS=false
   ```

5. Seed the database with sample flight data:

   ```bash
   python database/seed_flights.py
   ```

6. Start the app:

   ```bash
   python app.py
   ```

   The app will run on:

   ```text
   http://127.0.0.1:5000
   ```

## Running with Gunicorn

This project includes a `Procfile` for deployment:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

## Environment Variables

The app reads the following variables from `.env` or the system environment:

- `MONGO_URI` - MongoDB connection string
- `SECRET_KEY` - Flask secret key
- `MAIL_SERVER` - SMTP hostname
- `MAIL_PORT` - SMTP port
- `MAIL_USERNAME` - SMTP username
- `MAIL_PASSWORD` - SMTP password or app password
- `MAIL_DEFAULT_SENDER` - email address used as sender
- `MAIL_USE_SSL` - whether to use SSL
- `MAIL_USE_TLS` - whether to use TLS

## Notes

- For Gmail, you may need to create an app password instead of using your normal account password.
- If you are using MongoDB Atlas, make sure the IP address is allowed in your cluster network settings.
- The app expects a database named `AirBook` in MongoDB, as configured in `database/db.py`.

## Admin / Demo Usage

After the app is running:

1. Register a new user account.
2. Log in with the new account.
3. Use the flight search flow to book tickets.
4. Access admin features if your account has admin privileges or if the system has seeded admin users.

## License

This project is for educational/demo purposes unless a separate license is provided.


## Dev
NAME : POORNA DINESH H D
CONTACT : POORNA8217@GMAIL.COM