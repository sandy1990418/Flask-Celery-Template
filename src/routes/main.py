from flask import Blueprint, render_template

from src.models.controller import ReportsController

main_routes = Blueprint("main", __name__)


@main_routes.route("/home")
def home():
    project_info = ReportsController.get_project_model_data()
    return render_template("index.html", projects=project_info)
