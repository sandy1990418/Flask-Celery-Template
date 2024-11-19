from typing import Dict, List, Optional

import requests
from celery import chain

from src.celeryflow import celery_app
from src.celeryflow.celery_controller import (
    ControllerContext,
    create_evaluation_result,
    create_response_record,
)
from src.celeryflow.task_decorator import with_progress
from src.celeryflow.task_tracker import CeleryBaseTask
from src.models.controller import EvaluationController
from src.models.db_schema import QuestionData, ResultData
from src.utils.api_client import OpenAIClient
from src.utils.logger import logger


@celery_app.task(bind=True, name="template.check_health", base=CeleryBaseTask)
@with_progress("Checking health for API")
def check_health(
    api_health_endpoints: str = "https://status.openai.com/api/v2/status.json",
):
    """Check API health status and pass data if healthy"""

    logger.info(f"Checking health for API: {api_health_endpoints}")
    try:
        response = requests.get(api_health_endpoints)
        is_healthy = response.status_code == requests.codes.ok
        if is_healthy:
            logger.info("API health check!")
            return
    except Exception as e:
        logger.error(f"API health check error: {str(e)}")
    logger.error("API health check failed !")


@celery_app.task(
    bind=True, name="evaluation.tasks.get_question_datasets", base=CeleryBaseTask
)
@with_progress("get_question_dataset")
def get_question_dataset(self, test_paper: dict) -> List[dict]:
    logger.info("Get Question dataset for Evaluation.")

    controller = EvaluationController()

    question_version_id = controller.get_question_version_id(
        evaluation_type=test_paper["evaluation_type"],
        question_version=test_paper["version"],
    )

    question_data: List[QuestionData] = controller.get_question(
        question_version_id=question_version_id,
        question_category=test_paper["evaluation_type"],
    )

    test_paper["result"]["question_version_id"] = question_version_id

    evaluation_result_controller = ControllerContext.get_evaluation_controller()
    evaluation_result_controller.update_data(
        request_data=ResultData.from_dict(test_paper["result"])
    )

    test_paper.update({"data": []})
    question_data_list = []
    for each_question in question_data:
        temp_dict = each_question.__dict__
        temp_dict.update({"question_version_id": question_version_id})
        question_data_list.append(temp_dict)

    test_paper.update({"data": question_data_list})
    return test_paper


@celery_app.task(
    bind=True,
    name="evaluation.tasks.evaluation_pipeline",
    base=CeleryBaseTask,
    time_limit=3600,
)
@with_progress("evaluation_pipeline")
def evaluation_pipeline(self, test_paper: dict):
    logger.info(
        f"Processing evaluation for examinee model ID: {test_paper['model_id']}..."
    )

    # 陷阱：要用with_progress紀錄for loop內的內容要return something
    response_record_controller = ControllerContext.get_response_controller()
    wait_for_human = False
    question_data = test_paper.get("data")
    evaluation_response_list = []
    for each_question in question_data:
        response_record = create_response_record(test_paper["result"]["result_id"])

        response_record.question_id = each_question["question_id"]

        # 2. Call Student Model
        model_response = call_model(
            each_question=each_question,
            model_endpoint=test_paper["model_endpoint"],
        )
        response_record.model_response = model_response
        logger.debug(f"Answer set: {each_question['groundtruth_set']}")
        logger.debug(f"Student Response: {model_response}")
        logger.debug(f"Answer: {each_question['groundtruth_content']}")

        # 3. Call Evaluation Method (Teacher or Rule-Based)
        evaluation_response = do_evaluate(
            each_question=each_question,
            model_response=model_response,
            test_paper=test_paper,
        )
        response_record.model_response = evaluation_response
        evaluation_response_list.append(evaluation_response)

        response_record.status = 1
        response_record_controller.update_data(request_data=response_record)

    test_paper.update(
        {
            "wait_for_human": wait_for_human,
        }
    )
    logger.info("Finished Evaluation！")

    return evaluation_response_list


@celery_app.task(bind=True, base=CeleryBaseTask)
def record_result(self, test_paper):
    wait_for_human = test_paper.get("wait_for_human")
    evaluation_response_list = test_paper["evaluation_response_list"]
    score = compute_score(evaluation_response_list)

    test_paper["result"]["evaluation_score"] = score
    if wait_for_human:
        test_paper["result"]["status"] = 4
    else:
        test_paper["result"]["status"] = 1

    evaluation_result_controller = ControllerContext.get_evaluation_controller()
    evaluation_result_controller.update_data(
        request_data=ResultData.from_dict(test_paper["result"])
    )
    logger.info(f"Final Score: {score}")

    return {"result_id": test_paper["result"]["result_id"]}


def compute_score(content_list: list, correct_str="Correct"):
    correct_count = 0
    for content in content_list:
        if content == correct_str:
            correct_count += 1
    return int((correct_count / len(content_list)) * 100)  # 原本是小數點，乘 100 變成滿分一百分


def call_model(each_question: dict, model_endpoint: str):
    question = each_question["question_content"]

    if each_question["groundtruth_type"] == "Classification":
        ex_ans = list(eval(each_question["groundtruth_set"]))[0]
        question_prefix = "Please answer the following **single-choice question**, \
                           and strictly adhere to the [Response Format]:\nQuestion: "
        question_postfix = f"\n[Response Format]\nYour response must be one of the \
                           options in the following set, and the answer text must \
                           match the option exactly. For example, answer: {ex_ans}. \
                           Do not generate any extra symbols. Do not generate any extra characters."
        question = question_prefix + question + question_postfix

    elif each_question["groundtruth_type"] == "MultipleChoice":
        tmp = list(eval(each_question["groundtruth_type"]))
        ex_ans = tmp[0] + "/" + tmp[1]
        question_prefix = "Please answer the following **multiple-choice question**, \
                           and strictly adhere to the [Response Format]:\nQuestion: "
        question_postfix = f'\n[Response Format]\nYour response must be one or more \
                            options from the following set, with each selected option \
                            separated by a "/". The answer text must match the options \
                            exactly. For example, answer: {ex_ans}. Do not generate any \
                            extra symbols. Do not generate any extra characters.'
        question = question_prefix + question + question_postfix

    response = requests.post(
        model_endpoint,
        json={"input": question},
    )
    return response.json()["output"]


def do_evaluate(
    each_question: dict, model_response: str, test_paper: dict, max_retry=3
):
    try:
        groundtruth_set = eval(each_question["groundtruth_set"])
        groundtruth_content = each_question["groundtruth_content"]
        if model_response not in groundtruth_set:
            api_client = OpenAIClient(
                api_endpoint=test_paper["evaluation_model_endpoint"]
            )

            input_text = (
                f"RESPOND ONLY 'Correct' or 'Incorrect'."
                f"Compare if the text content SEMANTICALLY contains or indicates the same answer as the correct answer,"
                f"even if expressed differently or with additional explanation."
                f"\n[Text Content]: {model_response}"
                f"\n[Correct Answer]: {groundtruth_content}"
                f"\nIf the text clearly indicates or concludes with the same answer, respond 'Correct', "
                f"even if it includes additional explanation or reasoning."
            )
            call_count = 0
            evaluate_response = None
            while call_count < max_retry and evaluate_response not in {
                "Correct",
                "Incorrect",
            }:
                evaluate_response = api_client.do_request(
                    input_text=input_text,
                    model_name="gpt-4o",
                )
        else:
            evaluate_response = (
                "Correct" if model_response == groundtruth_content else "Incorrect"
            )
        return evaluate_response
    except Exception as e:
        logger.error(f"Error in do_evaluate: {e}")
        return ""


@celery_app.task(bind=True, base=CeleryBaseTask)
def start_evaluation_tasks(
    self, test_papers: List[dict], sync: Optional[bool] = False
) -> Dict:
    results = []
    task_sequence = []  # for single task
    for test_paper in test_papers:
        try:
            logger.info(f"Starting evaluation for model {test_paper['model_id']}")
            test_paper.update(
                {
                    "evaluation_model_endpoint": "https://api.openai.com/v1/chat/completions"
                }
            )

            create_evaluation_result(test_paper["result"])
            if not sync:  # default use asynchronize
                evaluation_chain = chain(
                    check_health.si(),
                    get_question_dataset.si(test_paper),
                    evaluation_pipeline.s(),
                    record_result.s(),
                )
                results.append(
                    {"Categories": test_paper, "chain_result": evaluation_chain()}
                )
            else:
                task = process_single_exam.signature(test_paper, immutable=True)
                task_sequence.append(task)
                if task_sequence:
                    chain(task_sequence)()

        except Exception as e:
            logger.error(f"Evaluation process failed: {str(e)}")
            evaluation_result_controller = ControllerContext.get_evaluation_controller()
            evaluation_result_controller.execute(
                request_data=test_paper["result"],
            )
            results.append(
                {
                    "status": "error",
                    "model_id": test_paper["model_id"],
                    "error": str(e),
                }
            )

    return results


@celery_app.task(bind=True, base=CeleryBaseTask)
def process_single_exam(self, test_paper) -> Dict:
    """
    Deal Single exam task
    """
    try:
        check_health(test_paper["model_endpoint"])

        dataset = get_question_dataset(test_paper)
        if not dataset:
            raise Exception("Failed to get question dataset")

        eval_result = evaluation_pipeline(dataset, test_paper)

        return {
            "status": "success",
            "Categories": test_paper,
            "chain_result": eval_result,
        }

    except Exception as e:
        logger.error(f"Exam processing failed: {str(e)}")
        raise
