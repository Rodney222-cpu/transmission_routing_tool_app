"""
Authentication routes for Transmission Line Routing Tool
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime

from app import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json() if request.is_json else request.form
    
    # Validate input
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    organization = data.get('organization', '')
    
    if not username or not email or not password:
        if request.is_json:
            return jsonify({'error': 'Missing required fields'}), 400
        flash('Missing required fields', 'error')
        return redirect(url_for('auth.register'))
    
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        if request.is_json:
            return jsonify({'error': 'Username already exists'}), 400
        flash('Username already exists', 'error')
        return redirect(url_for('auth.register'))
    
    if User.query.filter_by(email=email).first():
        if request.is_json:
            return jsonify({'error': 'Email already registered'}), 400
        flash('Email already registered', 'error')
        return redirect(url_for('auth.register'))
    
    # Create new user
    user = User(
        username=username,
        email=email,
        organization=organization
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': 'User registered successfully'}), 201
    
    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() if request.is_json else request.form
    
    username = data.get('username')
    password = data.get('password')
    remember = data.get('remember', False)
    
    if not username or not password:
        if request.is_json:
            return jsonify({'error': 'Missing credentials'}), 400
        flash('Missing credentials', 'error')
        return redirect(url_for('auth.login'))
    
    # Find user
    user = User.query.filter_by(username=username).first()
    
    if user is None or not user.check_password(password):
        if request.is_json:
            return jsonify({'error': 'Invalid username or password'}), 401
        flash('Invalid username or password', 'error')
        return redirect(url_for('auth.login'))
    
    # Log in user
    login_user(user, remember=remember)
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    if request.is_json:
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'organization': user.organization
            }
        })
    
    next_page = request.args.get('next')
    return redirect(next_page or url_for('main.dashboard'))


@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """User logout"""
    logout_user()
    
    if request.is_json:
        return jsonify({'message': 'Logged out successfully'})
    
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/user', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'organization': current_user.organization,
        'role': current_user.role,
        'created_at': current_user.created_at.isoformat()
    })

