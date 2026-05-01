from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from .models import db
import os

# Initialize extensions
socketio = SocketIO(cors_allowed_origins="*") 
jwt = JWTManager()
cors = CORS()

def init_extensions(app):
    # MongoDB Configuration
    app.config['MONGODB_SETTINGS'] = {
        'host': os.getenv('MONGODB_URI')
    }
    
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
