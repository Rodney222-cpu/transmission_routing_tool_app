"""
Main view routes for Transmission Line Routing Tool
"""
from flask import Blueprint, render_template, redirect, url_for, current_app
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with map interface"""
    return render_template(
        'dashboard.html',
        user=current_user,
        maptiler_key=current_app.config.get('MAPTILER_API_KEY') or '',
        thunderforest_key=current_app.config.get('THUNDERFOREST_API_KEY') or '',
    )

