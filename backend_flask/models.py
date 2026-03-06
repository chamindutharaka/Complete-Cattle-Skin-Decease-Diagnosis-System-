from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    role = db.Column(db.String(20), default="farmer")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    assigned_cattle = db.relationship('CattleStaff', backref='user', lazy=True)

class Cattle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    sensor_readings = db.relationship('SensorReading', backref='cattle', lazy=True, order_by="desc(SensorReading.created_at)")
    alerts = db.relationship('Alert', backref='cattle', lazy=True)
    assigned_staff = db.relationship('CattleStaff', backref='cattle', lazy=True)

class CattleStaff(db.Model):
    cattle_id = db.Column(db.Integer, db.ForeignKey('cattle.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    heart_rate = db.Column(db.Float, nullable=True)
    distance = db.Column(db.Float, nullable=True)
    spo2 = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cattle_id = db.Column(db.Integer, db.ForeignKey('cattle.id'), nullable=False)

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(50), nullable=False) # warning, critical, DL_Anomaly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cattle_id = db.Column(db.Integer, db.ForeignKey('cattle.id'), nullable=False)
