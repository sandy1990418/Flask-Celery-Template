import asyncio
import json

from flask import (  # make_response,
    Blueprint,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    stream_with_context,
    url_for,
)

from src.celeryflow.chain_monitor import get_chain_progress
from src.celeryflow.tasks import start_evaluation_tasks
from src.models.controller import BasicController, EvaluationController

# from src.controllers.reports_controller import ReportsController
from src.models.db_schema import ModelData
from src.utils.async2sync import async_generator_to_sync
from src.utils.logger import logger
from src.utils.task_status_db import update_task_state  # get_evaluation_result_id,
from src.utils.user_logger import user_logger  # , run_in_background, executor

evaluation_routes = Blueprint("evaluation", __name__)


@evaluation_routes.route("/evaluation_home", methods=["POST"])
@user_logger()
def evaluation_home():
    model_id = request.args.get("model_id")
    model_name = request.args.get("model_name")
    model_version = request.args.get("model_version")
    model_endpoint = request.args.get("model_endpoint")

    controller = EvaluationController()
    if controller.is_model_locked(model_id):
        return redirect(url_for("main.home"))

    # 如果有task_id的參數,先檢查任務狀態
    task_id = request.args.get("task_id")
    if task_id:
        try:
            task_info = async_generator_to_sync(get_chain_progress(task_id))
            if task_info["state"] in ["PENDING", "STARTED"]:
                return redirect(url_for("main.home"))
        except Exception as e:
            logger.error(f"Error checking task status: {str(e)}")

    # View Question Data and Evaluation Model Data
    exam_info = dict(controller.get_evaluation_version())
    evaluation_model = BasicController.get_all_data(db_schema=ModelData)

    return render_template(
        "evaluation.html",
        model_id=model_id,
        model_name=model_name,
        model_version=model_version,
        model_endpoint=model_endpoint,
        exam_info=exam_info,
        evaluation_model=evaluation_model,
    )


@evaluation_routes.route("/do_evaluate", methods=["GET", "POST"])
@user_logger()
def do_evaluate():
    controller = EvaluationController()
    test_papers = controller.prepare_exam(request, session)
    result = start_evaluation_tasks.delay(test_papers)

    logger.info("start")
    response = jsonify(
        {
            "status": "success",
            "message": "評測已開始",
            "task_id": result.id,
        }
    )
    response.headers.add("Access-Control-Allow-Origin", "*")  # 允許跨域請求

    # TODO: 要增加Evaluator API Key的部分
    # TODO: 不用等controller結束再回傳 去背景執行
    return response


@evaluation_routes.route("/cancelled_evaluate", methods=["GET"])
@user_logger()
def cancelled_evaluate():
    return redirect(url_for("main.home"))


@evaluation_routes.route("/evaluation_status_page/<task_id>", methods=["GET"])
@user_logger()
def evaluation_status_page(task_id):
    """Check the Evaluation Result Page"""
    try:
        # Get model information f
        model_id = request.args.get("model_id")
        model_name = request.args.get("model_name")
        model_version = request.args.get("model_version")
        return render_template(
            "status.html",
            task_id=task_id,
            model_id=model_id,
            model_name=model_name,
            model_version=model_version,
        )
    except Exception as e:
        logger.error(f"Error rendering status page: {str(e)}")
        return redirect(url_for("main.home"))


@evaluation_routes.route("/evaluation_status/<task_id>/stream")
@user_logger()
def evaluation_status(task_id):
    """
    Endpoint for streaming the evaluation status of a task to the client based on the task ID.
    """

    async def generate():
        """Asynchronous generator that yields task progress updates as server-sent events."""
        while True:
            try:
                # Retrieve current progress of the task
                task_info = await get_chain_progress(task_id, revoke=False)
                yield f"data: {json.dumps(task_info)}\n\n"
                # Stop streaming when the task is completed or failed
                if task_info["state"] in ["SUCCESS", "FAILED", "TERMINATED"]:
                    break
                # Delay between status checks to avoid overloading the server with requests
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in stream: {str(e)}")  # 調試日誌
                break

    def sync_generate():
        """Synchronous generator wrapper for the asynchronous generator."""
        for item in async_generator_to_sync(generate()):
            yield item

    return Response(
        stream_with_context(sync_generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",  # Disable caching to ensure real-time updates
            "Connection": "keep-alive",  # Keep connection open for streaming
            "Access-Control-Allow-Origin": "*",  # Allow cross-origin requests
            "Access-Control-Allow-Methods": "POST",  # Allow POST method for this route
            "Access-Control-Allow-Headers": "Content-Type",  # Allow 'Content-Type' header in requests
        },
    )


@evaluation_routes.route("/terminate_task/<task_id>/terminate", methods=["POST"])
@user_logger()
def terminate_task(task_id: str):
    try:
        # 調用 get_chain_progress 並設置 revoke=True
        result = asyncio.run(get_chain_progress(task_id, revoke=True))

        return jsonify(
            {"success": True, "message": "Tasks have been terminated", "result": result}
        )

    except Exception as e:
        logger.error(f"Error in terminate_task: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@evaluation_routes.route("/pause/<task_id>", methods=["POST"])
@user_logger()
def pause(task_id):
    success_pause = update_task_state(task_id, "PAUSED", True)
    if success_pause:
        return jsonify(
            {
                "status": "paused",
                "task_id": task_id,
                "is_paused": True,
                "state": "PAUSED",
            }
        )
    return jsonify({"status": "error"})


@evaluation_routes.route("/resume/<task_id>", methods=["POST"])
@user_logger()
def resume(task_id):
    success_resume = update_task_state(task_id, "PROGRESS", False)
    if success_resume:
        return jsonify(
            {
                "status": "resumed",
                "task_id": task_id,
                "is_paused": False,
                "state": "PROGRESS",
            }
        )
    return jsonify({"status": "error"})


# @evaluation_routes.route("/export/<task_id>", methods=["POST"])
# @user_logger()
# def export(task_id):
#     evaluation_result_id = get_evaluation_result_id(task_id)
#     manual_quesiton_data = ReportsController.get_manual_quesiton_data(
#         evaluation_result_id["evaluation_result_ids"]
#     )
#     response = make_response(manual_quesiton_data.to_csv(index=False))
#     response.headers[
#         "Content-Disposition"
#     ] = "attachment; filename=evaluation_export.csv"
#     response.headers["Content-type"] = "text/csv"
#     return response
