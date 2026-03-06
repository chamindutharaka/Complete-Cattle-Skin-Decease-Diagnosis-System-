from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from .models import db

# Initialize extensions
# cors_allowed_origins="*" allows the frontend (port 5173) to connect to backend (port 5001) without issues
socketio = SocketIO(cors_allowed_origins="*") 
jwt = JWTManager()
cors = CORS()

def init_extensions(app):
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    # Allow all origins, all headers, all methods for /api routes
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
    
    with app.app_context():
        db.create_all()
