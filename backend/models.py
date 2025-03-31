from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    handled = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'type': self.type,
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'handled': self.handled
        }

class SecurityAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    ip_address = db.Column(db.String(45))
    geolocation_data = db.Column(db.JSON)
    intruder_image = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) 