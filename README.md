# Flask-Celery-Template

A project template integrating Flask and Celery for handling asynchronous tasks and background jobs, with a focus on task progress tracking.

## Features

- **Flask**: A lightweight WSGI web application framework.
- **Celery**: Asynchronous task queue/job queue based on distributed message passing.
- **SQLite**: Used as the database for storing application data.
- **Task Progress Tracking**: Monitor the progress of Celery tasks and display their current status in the system log.

## Requirements

- Python 3.8+

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/flask-celery-template.git
   cd flask-celery-template
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask application:
   ```bash
   python app_run.py
   ```

2. Start the Celery worker:
   ```bash
   celery -A src.celeryflow.celery_app worker --loglevel=info
   ```

3. Monitor task progress in the system log to see real-time updates on task status.


## License

This project is licensed under the MIT License.
