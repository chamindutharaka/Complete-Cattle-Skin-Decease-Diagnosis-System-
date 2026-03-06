import os
from flask import Flask
from backend_flask.extensions import init_extensions, socketio
from backend_flask.routes.auth import auth_bp
from backend_flask.routes.cattle import cattle_bp
from backend_flask.routes.data import data_bp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False # Allow /api/cattle and /api/cattle/ to work the same
    
    # Configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'models_data', 'flask_app.db')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'super-secret-research-key')
    app.config['SECRET_KEY'] = 'another-secret-key' # Required for sessions/socketio

    # Initialize Extensions (DB, JWT, SocketIO, CORS)
    init_extensions(app)

    # Register Blueprints (Routes)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(cattle_bp, url_prefix='/api/cattle')
    app.register_blueprint(data_bp, url_prefix='/api/data')

    @app.route('/')
    def index():
        return "Flask Backend for Cattle Anomaly Detection is Running!"

    return app

if __name__ == '__main__':
    app = create_app()
    # Use socketio.run instead of app.run for WebSocket support
    socketio.run(app, host='0.0.0.0', port=5006, debug=True)
