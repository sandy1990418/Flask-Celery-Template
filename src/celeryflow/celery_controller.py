from src.models.controller import BasicController
from src.models.db_schema import ResultData, ResultRecordData
from src.utils.data_handler import IdentityHandler


class ControllerContext:
    @staticmethod
    def get_evaluation_controller() -> BasicController:
        return BasicController(
            request_handler=IdentityHandler(align_dataclass=ResultData)
        )

    @staticmethod
    def get_response_controller() -> BasicController:
        return BasicController(
            request_handler=IdentityHandler(align_dataclass=ResultRecordData)
        )


def create_evaluation_result(evaluation_result: dict) -> None:
    evaluation_result_controller = ControllerContext.get_evaluation_controller()

    evaluation_result_controller.add_data(
        request_data=ResultData.from_dict(evaluation_result)
    )

    if (
        evaluation_result_controller.repository.metadata["LastOperation"]["Status"]
        == "Failed"
    ):
        raise ValueError("Evaluation Failed: Cannot create a new evaluation result.")
    else:
        id = evaluation_result_controller.repository.metadata["LastOperation"][
            "OperationID"
        ]
        evaluation_result.update({"result_id": id})


def create_response_record(result_id: int) -> ResultRecordData:
    response_record = ResultRecordData(
        result_record_id=result_id,
        result_id="TBD",
        question_id="TBD",
        model_response="TBD",
    )

    response_record_controller = ControllerContext.get_response_controller()

    response_record_controller.add_data(response_record)

    if (
        response_record_controller.repository.metadata["LastOperation"]["Status"]
        == "Failed"
    ):
        raise ValueError("Evaluation Failed: Cannot create a new response record.")
    else:
        id = response_record_controller.repository.metadata["LastOperation"][
            "OperationID"
        ]
        response_record.result_record_id = id
    return response_record
