from src.routes.evaluation import evaluation_routes
from src.routes.main import main_routes
from src.routes.model import model_routes
from src.routes.project import project_routes
from src.routes.user import user_routes

__all__ = [
    "project_routes",
    "user_routes",
    "main_routes",
    "model_routes",
    "evaluation_routes",
]
