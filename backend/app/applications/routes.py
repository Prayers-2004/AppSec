from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Application, db

bp = Blueprint('applications', __name__)

@bp.route('/', methods=['GET'])
@jwt_required()
def get_applications():
    current_user_id = get_jwt_identity()
    applications = Application.query.filter_by(user_id=current_user_id).all()
    return jsonify([{
        'id': app.id,
        'name': app.name,
        'path': app.path,
        'is_protected': app.is_protected,
        'created_at': app.created_at.isoformat()
    } for app in applications])

@bp.route('/', methods=['POST'])
@jwt_required()
def add_application():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    application = Application(
        name=data['name'],
        path=data['path'],
        is_protected=data.get('is_protected', True),
        user_id=current_user_id
    )
    
    db.session.add(application)
    db.session.commit()
    
    return jsonify({
        'id': application.id,
        'name': application.name,
        'path': application.path,
        'is_protected': application.is_protected,
        'created_at': application.created_at.isoformat()
    }), 201

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_application(id):
    current_user_id = get_jwt_identity()
    application = Application.query.filter_by(id=id, user_id=current_user_id).first()
    
    if not application:
        return jsonify({'error': 'Application not found'}), 404
        
    data = request.get_json()
    
    if 'name' in data:
        application.name = data['name']
    if 'path' in data:
        application.path = data['path']
    if 'is_protected' in data:
        application.is_protected = data['is_protected']
        
    db.session.commit()
    
    return jsonify({
        'id': application.id,
        'name': application.name,
        'path': application.path,
        'is_protected': application.is_protected,
        'created_at': application.created_at.isoformat()
    })

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_application(id):
    current_user_id = get_jwt_identity()
    application = Application.query.filter_by(id=id, user_id=current_user_id).first()
    
    if not application:
        return jsonify({'error': 'Application not found'}), 404
        
    db.session.delete(application)
    db.session.commit()
    
    return jsonify({'message': 'Application deleted successfully'})

@bp.route('/<int:id>/verify', methods=['POST'])
@jwt_required()
def verify_application_access(id):
    current_user_id = get_jwt_identity()
    application = Application.query.filter_by(id=id, user_id=current_user_id).first()
    
    if not application:
        return jsonify({'error': 'Application not found'}), 404
        
    if not application.is_protected:
        return jsonify({'access': True})
        
    # Here you would implement additional verification logic
    # For example, checking if the user has the right permissions
    # or if the application is currently locked
    
    return jsonify({'access': True}) 