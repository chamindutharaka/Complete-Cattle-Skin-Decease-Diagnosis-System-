from flask_mongoengine import MongoEngine
from datetime import datetime

db = MongoEngine()

class User(db.Document):
    username = db.StringField(unique=True, required=True)
    password = db.StringField(required=True)
    phone = db.StringField(unique=True)
    role = db.StringField(default="farmer")
    created_at = db.DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'users'}

class Cattle(db.Document):
    device_id = db.StringField(unique=True, required=True)
    name = db.StringField(required=True)
    created_at = db.DateTimeField(default=datetime.utcnow)
    updated_at = db.DateTimeField()

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Cattle, self).save(*args, **kwargs)

    meta = {'collection': 'cattle'}

class SensorReading(db.Document):
    temperature = db.FloatField(required=True)
    humidity = db.FloatField(required=True)
    heart_rate = db.FloatField()
    distance = db.FloatField()
    spo2 = db.FloatField()
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    cattle = db.ReferenceField('Cattle', reverse_delete_rule=db.CASCADE)

    meta = {
        'collection': 'sensor_readings',
        'indexes': ['cattle', '-created_at']
    }

class Alert(db.Document):
    message = db.StringField(required=True)
    level = db.StringField(required=True) # warning, critical, dl_anomaly
    created_at = db.DateTimeField(default=datetime.utcnow)
    
    cattle = db.ReferenceField('Cattle', reverse_delete_rule=db.CASCADE)

    meta = {
        'collection': 'alerts',
        'indexes': ['cattle', '-created_at']
    }

class CattleStaff(db.Document):
    cattle = db.ReferenceField('Cattle', required=True)
    user = db.ReferenceField('User', required=True)
    assigned_at = db.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'cattle_staff',
        'indexes': [('cattle', 'user')]
    }
