from flask import Flask
from pymongo import MongoClient
import config

client = MongoClient(config.MONGODB_URI)
db = client[config.MONGODB_NAME]

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = config.SECRET_KEY

    # import and register our routes
    from .routes import main
    app.register_blueprint(main)

    return app
