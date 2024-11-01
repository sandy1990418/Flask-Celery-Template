from flask import Blueprint

main_routes = Blueprint("main", __name__)


@main_routes.route("/home")
def home():
    pass
    # return render_template("main.html")
