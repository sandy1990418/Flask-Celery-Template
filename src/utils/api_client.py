import os
from abc import ABC, abstractmethod

import requests


class APIClient(ABC):
    def __init__(self, api_endpoint=None):
        if not os.environ.get(self.api_key_name):
            raise ValueError(f"{self.api_key_name} is not found in environment.")

        self.api_endpoint = api_endpoint or self.default_api_endpoint

        self.check_health()

    @property
    @abstractmethod
    def api_key_name(self):
        pass

    @property
    @abstractmethod
    def default_api_endpoint(self):
        pass

    @property
    @abstractmethod
    def default_model_name(self):
        pass

    @property
    def headers(self):
        return {
            "Authorization": f"Bearer {os.environ.get(self.api_key_name)}",
            "Content-Type": "application/json",
        }

    @abstractmethod
    def format_output(self, response):
        pass

    @abstractmethod
    def format_input(self, input_text, model_name=None, **kwargs):
        pass

    def check_health(self):
        self.do_request("Say your Name")

    def do_request(self, input_text, model_name=None):
        formatted_input = self.format_input(input_text, model_name)
        response = requests.post(
            self.api_endpoint,
            headers=self.headers,
            json=formatted_input,
        )
        if response.status_code == 200:
            return self.format_output(response)
        else:
            raise ValueError(
                "Error in api check helth: ", response.status_code, response.text
            )


class OpenAIClient(APIClient):
    @property
    def api_key_name(self):
        return "OPENAI_API_KEY"

    @property
    def default_api_endpoint(self):
        return "https://api.openai.com/v1/chat/completions"

    @property
    def default_model_name(self):
        return "gpt-4o-mini"

    def format_input(self, input_text, model_name=None, **kwargs):
        model_name = model_name or self.default_model_name
        return {
            "model": model_name,
            "messages": [{"role": "user", "content": input_text}],
        }

    def format_output(self, response):
        return response.json()["choices"][0]["message"]["content"]
