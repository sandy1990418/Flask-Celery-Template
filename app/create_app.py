from dotenv import load_dotenv
from flask import Flask

from routes import main_routes, response_routes

load_dotenv(dotenv_path="./.env")


def create_app():
    app = Flask(__name__, template_folder="./templates")
    app.register_blueprint(main_routes)
    app.register_blueprint(response_routes)
    return app
