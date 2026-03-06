from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend_flask.models import db, Cattle, SensorReading, Alert

cattle_bp = Blueprint('cattle', __name__)

@cattle_bp.route('/', methods=['GET'])
def get_all_cattle():
    cattle_list = Cattle.query.all()
    result = []
    for c in cattle_list:
        # Get latest sensor reading for the dashboard summary
        latest = SensorReading.query.filter_by(cattle_id=c.id).order_by(SensorReading.created_at.desc()).first()
        readings = []
        if latest:
            readings.append({
                "id": latest.id,
                "temperature": latest.temperature,
                "humidity": latest.humidity,
                "heartRate": latest.heart_rate,
                "distance": latest.distance,
                "createdAt": latest.created_at.isoformat()
            })
            
        result.append({
            "id": c.id,
            "deviceId": c.device_id,
            "name": c.name,
            "sensorReadings": readings
        })
    return jsonify(result), 200

@cattle_bp.route('/', methods=['POST'])
@jwt_required()
def add_cattle():
    data = request.get_json()
    name = data.get('name')
    device_id = data.get('deviceId')
    
    if not name or not device_id:
        return jsonify({"message": "Name and Device ID required"}), 400
        
    if Cattle.query.filter_by(device_id=device_id).first():
        return jsonify({"message": "Device ID already registered"}), 400
        
    new_cattle = Cattle(name=name, device_id=device_id)
    db.session.add(new_cattle)
    db.session.commit()
    
    return jsonify({
        "id": new_cattle.id, 
        "name": new_cattle.name, 
        "deviceId": new_cattle.device_id,
        "sensorReadings": []
    }), 201

@cattle_bp.route('/<int:id>', methods=['GET'])
def get_cattle(id):
    cattle = Cattle.query.get_or_404(id)
    readings = SensorReading.query.filter_by(cattle_id=id).order_by(SensorReading.created_at.desc()).limit(100).all()
    alerts = Alert.query.filter_by(cattle_id=id).order_by(Alert.created_at.desc()).limit(20).all()
    
    return jsonify({
        "id": cattle.id,
        "name": cattle.name,
        "deviceId": cattle.device_id,
        "sensorReadings": [{
            "id": r.id,
            "temperature": r.temperature,
            "humidity": r.humidity,
            "heartRate": r.heart_rate,
            "distance": r.distance,
            "createdAt": r.created_at.isoformat()
        } for r in readings],
        "alerts": [{
            "id": a.id,
            "message": a.message,
            "level": a.level,
            "createdAt": a.created_at.isoformat()
        } for a in alerts]
    })
