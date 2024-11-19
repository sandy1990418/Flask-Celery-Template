from flask import Blueprint

response_routes = Blueprint("main", __name__)


@response_routes.route("/response")
def response():
    pass
    # return render_template("main.html")
