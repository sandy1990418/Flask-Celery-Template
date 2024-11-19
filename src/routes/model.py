from flask import Blueprint, redirect, request, url_for

from src.models.controller import BasicController
from src.models.db_schema import ModelData
from src.utils.data_handler import RequestHandler
from src.utils.user_logger import user_logger

model_routes = Blueprint("model", __name__)


@model_routes.route("/add_model", methods=["POST"])
@user_logger()
def add_model():
    controller = BasicController(
        request_handler=RequestHandler(align_dataclass=ModelData)
    )
    controller.add_data(request_data=request)
    return redirect(url_for("main.home"))


@model_routes.route("/update_model", methods=["POST"])
@user_logger()
def update_model():
    controller = BasicController(
        request_handler=RequestHandler(align_dataclass=ModelData)
    )
    controller.update_data(request_data=request)
    return redirect(url_for("main.home"))


@model_routes.route("/delete_model", methods=["POST"])
@user_logger()
def delete_model():
    controller = BasicController(
        request_handler=RequestHandler(align_dataclass=ModelData)
    )
    controller.delete_data(request_data=request)
    return redirect(url_for("main.home"))
