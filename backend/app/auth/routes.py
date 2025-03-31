from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User, db
from app.security import capture_image, get_location, send_alert_email

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
        
    user = User(email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        # Record failed attempt
        from app.models import LoginAttempt
        attempt = LoginAttempt(
            user_id=user.id if user else None,
            success=False,
            ip_address=request.remote_addr,
            location=get_location(request.remote_addr)
        )
        db.session.add(attempt)
        db.session.commit()
        
        # Check if max attempts reached
        failed_attempts = LoginAttempt.query.filter_by(
            user_id=user.id if user else None,
            success=False
        ).count()
        
        if failed_attempts >= 3:
            # Capture image and send alert
            image_path = capture_image()
            send_alert_email(user.email, image_path, attempt.location)
            
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Record successful attempt
    attempt = LoginAttempt(
        user_id=user.id,
        success=True,
        ip_address=request.remote_addr,
        location=get_location(request.remote_addr)
    )
    db.session.add(attempt)
    db.session.commit()
    
    access_token = create_access_token(identity=user.id)
    return jsonify({'access_token': access_token}), 200

@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({
        'id': user.id,
        'email': user.email,
        'created_at': user.created_at.isoformat()
    }) 