# Project: Shiksha-AI

## Project Overview

This is a Django-based web application named "Shiksha-AI". Based on the application names (`accounts`, `core`, `skills`, `users`), it appears to be an educational or skill-development platform. The project is in its early stages of development.

The project uses a custom user model and is configured to use a SQLite database. It also integrates with Firebase for backend services.

**Key Technologies:**

*   **Backend:** Django
*   **Database:** SQLite
*   **Other:** Firebase

## Building and Running

### Prerequisites

*   Python 3.11
*   Pip
*   Virtualenv

### Setup

1.  **Clone the repository.**
2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

```bash
python scripts/_sample_data.py
```

4.  **Create a `.env` file** in the project root and add the following, replacing the placeholder values:

    ```
    SECRET_KEY=your-secret-key
    DEBUG=True
    FIREBASE_CREDENTIALS_FILE=path/to/your/firebase-credentials.json
    FIREBASE_PROJECT_ID=your-firebase-project-id
    ```

### Running the application

1.  **Apply the database migrations:**

    ```bash
    python manage.py migrate
    ```

2.  **Run the development server:**

    ```bash
    python manage.py runserver
    ```

The application will be available at `http://127.0.0.1:8000`.

### Testing

To run the tests, use the following command:

```bash
python manage.py test
```

## Development Conventions

*   The project follows a standard Django project structure, with different functionalities separated into apps (`accounts`, `core`, `skills`, `users`).
*   A custom user model is defined in the `users` app.
*   Environment variables are used for configuration, managed via a `.env` file.
*   The code contains comments in both English and Marathi.
