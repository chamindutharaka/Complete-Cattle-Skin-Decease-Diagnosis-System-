import os
import json
import flask.json

# compatibility fix for flask 3.0+ which removed jsonencoder and jsondecoder
try:
    from flask.json import JSONEncoder
except ImportError:
    class JSONEncoder(json.JSONEncoder):
        pass
    flask.json.JSONEncoder = JSONEncoder

try:
    from flask.json import JSONDecoder
except ImportError:
    class JSONDecoder(json.JSONDecoder):
        pass
    flask.json.JSONDecoder = JSONDecoder

from flask import Flask
# restore removed attributes for flask-mongoengine compatibility
if not hasattr(Flask, 'json_encoder'):
    Flask.json_encoder = JSONEncoder
if not hasattr(Flask, 'json_decoder'):
    Flask.json_decoder = JSONDecoder

from backend_flask.extensions import init_extensions, socketio
from backend_flask.routes.auth import auth_bp
from backend_flask.routes.cattle import cattle_bp
from backend_flask.routes.data import data_bp
from dotenv import load_dotenv

# load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    
    # config
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-research-key')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'another-secret-key')

    # init extensions (mongodb, jwt, socketio, cors)
    init_extensions(app)

    # register blueprints (routes)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cattle_bp, url_prefix='/api/cattle')
    app.register_blueprint(data_bp, url_prefix='/api/data')

    @app.route('/')
    def index():
        return "Flask Backend for Cattle Anomaly Detection is Running!"

    return app

if __name__ == '__main__':
    app = create_app()
    # use socketio.run instead of app.run for websocket support
    socketio.run(app, host='0.0.0.0', port=5006, debug=True)
