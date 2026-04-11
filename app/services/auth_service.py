"""Authentication Service"""
import secrets
import jwt
from datetime import datetime, timedelta
from app.models.otp import OTP
from app.extensions import db
import string
import os


class AuthService:
    """Authentication Service"""
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    
    @staticmethod
    def generate_otp(length=6):
        """Generate random OTP"""
        otp = ''.join(secrets.choice(string.digits) for _ in range(length))
        return otp
    
    @staticmethod
    def create_otp_for_user(user_id):
        """Create and save OTP for user"""
        otp_code = AuthService.generate_otp()
        otp = OTP(
            user_id=user_id,
            otp_code=otp_code
        )
        db.session.add(otp)
        db.session.commit()
        return otp_code
    
    @staticmethod
    def verify_otp(user_id, otp_code):
        """Verify OTP for user"""
        try:
            otp = OTP.query.filter_by(user_id=user_id, otp_code=otp_code).first()
            if otp and otp.is_valid():
                otp.is_used = True
                db.session.commit()
                return True
            return False
        except Exception as e:
            print(f"OTP verification failed: {str(e)}")
            return False
    
    @staticmethod
    def generate_reset_token(user_id, expires_in=3600):
        """Generate password reset token"""
        payload = {
            'user_id': str(user_id),
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, AuthService.SECRET_KEY, algorithm='HS256')
        return token
    
    @staticmethod
    def verify_reset_token(token):
        """Verify reset token"""
        try:
            payload = jwt.decode(token, AuthService.SECRET_KEY, algorithms=['HS256'])
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError:
            print("Invalid token")
            return None
    
    @staticmethod
    def generate_password_reset_token():
        """Generate a random password reset token"""
        return secrets.token_urlsafe(32)