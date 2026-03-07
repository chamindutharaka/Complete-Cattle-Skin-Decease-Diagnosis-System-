from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from backend_flask.models import Cattle, SensorReading, Alert

cattle_bp = Blueprint('cattle', __name__)

@cattle_bp.route('/', methods=['GET'])
def get_all_cattle():
    cattle_list = Cattle.objects()
    result = []
    for c in cattle_list:
        # Get latest sensor reading for the dashboard summary
        latest = SensorReading.objects(cattle=c).order_by('-created_at').first()
        readings = []
        if latest:
            readings.append({
                "id": str(latest.id),
                "temperature": latest.temperature,
                "humidity": latest.humidity,
                "heartRate": latest.heart_rate,
                "distance": latest.distance,
                "createdAt": latest.created_at.isoformat()
            })
            
        result.append({
            "id": str(c.id),
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
        
    if Cattle.objects(device_id=device_id).first():
        return jsonify({"message": "Device ID already registered"}), 400
        
    new_cattle = Cattle(name=name, device_id=device_id)
    new_cattle.save()
    
    return jsonify({
        "id": str(new_cattle.id), 
        "name": new_cattle.name, 
        "deviceId": new_cattle.device_id,
        "sensorReadings": []
    }), 201

@cattle_bp.route('/<id>', methods=['GET'])
def get_cattle(id):
    try:
        cattle = Cattle.objects.get(id=id)
    except Exception:
        return jsonify({"message": "Cattle not found"}), 404
        
    readings = SensorReading.objects(cattle=cattle).order_by('-created_at').limit(100)
    alerts = Alert.objects(cattle=cattle).order_by('-created_at').limit(20)
    
    return jsonify({
        "id": str(cattle.id),
        "name": cattle.name,
        "deviceId": cattle.device_id,
        "sensorReadings": [{
            "id": str(r.id),
            "temperature": r.temperature,
            "humidity": r.humidity,
            "heartRate": r.heart_rate,
            "distance": r.distance,
            "createdAt": r.created_at.isoformat()
        } for r in readings],
        "alerts": [{
            "id": str(a.id),
            "message": a.message,
            "level": a.level,
            "createdAt": a.created_at.isoformat()
        } for a in alerts]
    })
