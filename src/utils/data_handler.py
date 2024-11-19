from abc import ABC, abstractmethod
from copy import deepcopy

from flask import Request

from src.models.db_schema import BaseSchema
from src.utils.logger import logger


class BaseHandler(ABC):
    def __init__(self, align_dataclass: BaseSchema):
        self.align_dataclass = align_dataclass

    @abstractmethod
    def process_data(self):
        raise NotImplementedError("Please Implement this method of `BaseHandler`.")


class RequestHandler(BaseHandler):
    def process_data(self, request_data: Request) -> BaseSchema:
        request_args = deepcopy(dict(request_data.args))
        request_form = deepcopy(dict(request_data.form))
        if same_key := request_args.keys() & request_form.keys():
            logger.warning(
                f"Variable ‘{same_key}’ is reused, may lead to unexpected behavior. Default use the following setting:"
            )
            for k, v in request_form.items():
                logger.warning(f"Variable {k}: {v}.")

        request_args.update(request_form)
        return self.align_dataclass.from_dict(request_args)


class IdentityHandler(BaseHandler):
    def process_data(self, data: BaseSchema):
        return data
