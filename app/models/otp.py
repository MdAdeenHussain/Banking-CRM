"""OTP Model for 2FA"""
from app.extensions import db
from datetime import datetime, timedelta
import uuid


class OTP(db.Model):
    """One-Time Password for 2FA"""
    __tablename__ = 'otps'
    
    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False, index=True)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(minutes=10))
    
    # Relationships
    user = db.relationship('User', backref='otps')
    
    def is_valid(self):
        """Check if OTP is valid and not expired"""
        return not self.is_used and datetime.utcnow() < self.expires_at
    
    def __repr__(self):
        return f'<OTP {self.user_id}>'
