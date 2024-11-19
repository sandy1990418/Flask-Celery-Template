from flask import Blueprint, redirect, render_template, request, url_for

from src.models.controller import EvaluationController
from src.models.db_schema import PersonData
from src.utils.data_handler import RequestHandler
from src.utils.user_logger import user_logger

user_routes = Blueprint("user", __name__)


@user_routes.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        controller = EvaluationController(
            request_handler=RequestHandler(align_dataclass=PersonData)
        )
        button_action = request.form.get("button_action")

        if button_action == "update_password":
            controller.update_data(request)
            return redirect(url_for("user.login"))
        else:
            if controller.is_evaluator_exist(request):
                return "The username is already be registed.", 200
            else:
                controller.add_data(request)

                return redirect(url_for("user.login"))

    return render_template("register.html")


@user_routes.route("/register_page", methods=["GET", "POST"])
def register_page():
    return render_template("register.html")


@user_routes.route("/", methods=["GET", "POST"])
def login():
    return render_template("login.html")


@user_routes.route("/check", methods=["GET", "POST"])
@user_logger()
def check():
    if request.method == "POST":
        controller = EvaluationController(
            request_handler=RequestHandler(align_dataclass=PersonData)
        )

        if controller.is_login_success(request):
            return redirect(url_for("main.home"))
        return "Invalid username or password", 200

    return render_template("login.html")
