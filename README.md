# Flask-Celery-System-Template

A project template integrating Flask and Celery for handling asynchronous tasks and background jobs, with a focus on task progress tracking. Currently implemented with MMMLU (Massive Multitask Language Understanding) benchmark evaluation capabilities.

## 🌟 Features

- 🚀 Built with Flask + Celery + RabbitMQ for reliable distributed processing

- 📊 Task execution tracking with detailed status updates


## 📁 Project Structure

```bash
.
├── src/
│   ├── celeryflow/      # Celery task management and processing
│   ├── models/          # Database models and operations
│   ├── routes/          # API routes and endpoints
│   ├── templates/       # HTML templates
│   └── utils/           # Utility functions and helpers
├── db/                  # Database initialization and drivers
├── docker/              # Docker and deployment configurations
├── app_run.py           # Flask Application python script
├── requirements.txt     # Project dependencies
└── config.yaml          # Application configuration
```


## 📦 Requirements

- Python 3.8+

## 🛠️ Installation

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






## 🚀 Usage

### Setting up RabbitMQ
   ```bash
   # Pull RabbitMQ image (first time only)
   docker pulll rabbitmq:management

   # Start RabbitMQ container
   docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:management
   ```

### Starting the System
   1. Start the Flask application:
      ```bash
      python app_run.py
      ```

   2. Start the Celery worker:
      ```bash
      # Start Celery worker with purge option
      celery -A app_run.celery_app worker

      # Start Flower for Celery monitoring
      celery -A app_run.celery_app flower
      ```
      Celery command options explained:

      `-A`: Specify the Celery app location <br>
      `-Q`: Specify which queues this worker should listen to<br>
      `-E`: Enable event tracking (logs task execution events)<br>
      `--pool=solo`: Run in single-thread mode<br>
      `--purge`: Clear all queued tasks before starting<br>
      `--loglevel=info`: Set logging level to info<br>

   3. Access the interfaces:
   - Web Application: `http://localhost:5000`
   - RabbitMQ Management: `http://localhost:15672` (default credentials: guest/guest)
   - Flower Dashboard: `http://localhost:5555`

## 🐳 Usage with Docker Compose

### Quick Start
```bash
# Start all services
docker compose -f ./docker/docker-compose.yaml up

# Start in detached mode
docker compose -f ./docker/docker-compose.yaml up -d
```



## 🙏 Acknowledgments

- OpenAI for the MMMLU benchmark
- Flask and Celery communities for their excellent frameworks
- Claude 3.5 Sonnet for assisting with the fronted

## License

This project is licensed under the MIT License.
