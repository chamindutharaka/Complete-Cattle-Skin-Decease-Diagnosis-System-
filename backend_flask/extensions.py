from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from .models import db
import os

# init extensions
socketio = SocketIO(cors_allowed_origins="*") 
jwt = JWTManager()
cors = CORS()

def init_extensions(app):
    # mongodb config
    app.config['MONGODB_SETTINGS'] = {
        'host': os.getenv('MONGODB_URI')
    }
    
    db.init_app(app)
    jwt.init_app(app)
    socketio.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)
