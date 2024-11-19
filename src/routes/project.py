from flask import Blueprint, redirect, render_template, request, url_for

from src.models.controller import BasicController, ReportsController
from src.models.db_schema import ProjectData
from src.utils.data_handler import RequestHandler
from src.utils.user_logger import user_logger

project_routes = Blueprint("project", __name__)


@project_routes.route("/add", methods=["POST"])
@user_logger()
def add_project():
    controller = BasicController(
        request_handler=RequestHandler(align_dataclass=ProjectData)
    )
    controller.add_data(request_data=request)
    return redirect(url_for("main.home"))


@project_routes.route("/update_project", methods=["POST"])
@user_logger()
def update_project():
    controller = BasicController(
        request_handler=RequestHandler(align_dataclass=ProjectData)
    )
    controller.update_data(request_data=request)
    return redirect(url_for("main.home"))


@project_routes.route("/delete_project", methods=["POST"])
@user_logger()
def delete_project():
    controller = BasicController(
        request_handler=RequestHandler(align_dataclass=ProjectData)
    )
    controller.delete_data(request_data=request)
    return redirect(url_for("main.home"))


@project_routes.route("/return_home", methods=["POST"])
@user_logger()
def return_home():
    action_type = request.form.get("button_action")

    if action_type == "return to home":
        return redirect(url_for("main.home"))
        # return result
    else:
        pass
    return redirect(url_for("main.home"))


@project_routes.route("/history_record", methods=["POST"])
@user_logger()
def history_record_project():
    action_type = request.form.get("button_action")
    project_id = int(request.args.get("from_project_id"))

    if action_type == "history_record":
        result = ReportsController.get_project_history_data_by_id(project_id=project_id)
        return render_template(
            "history.html",
            project_name=request.args.get("project_name"),
            columns=result.columns.tolist(),
            data=result.values.tolist(),
        )
    else:
        pass
    return redirect(url_for("main.home"))
