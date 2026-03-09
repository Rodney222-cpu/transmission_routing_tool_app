"""
Database models for Transmission Line Routing Optimization Tool
"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
import json


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(120))  # e.g., UETCL
    role = db.Column(db.String(20), default='user')  # user, admin, engineer
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    projects = db.relationship('Project', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Project(db.Model):
    """Project model for transmission line routing projects"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    voltage_level = db.Column(db.Integer, default=400)  # kV
    tower_type = db.Column(db.String(50), default='lattice')
    
    # Start and end points
    start_lat = db.Column(db.Float, nullable=False)
    start_lon = db.Column(db.Float, nullable=False)
    start_name = db.Column(db.String(100))
    
    end_lat = db.Column(db.Float, nullable=False)
    end_lon = db.Column(db.Float, nullable=False)
    end_name = db.Column(db.String(100))
    
    # AHP weights (stored as JSON)
    ahp_weights = db.Column(db.Text)  # JSON string

    # Additional project data (waypoints, etc.)
    project_metadata = db.Column(db.Text)  # JSON string for flexible metadata storage

    # Status
    status = db.Column(db.String(20), default='draft')  # draft, processing, completed, failed

    # User reference
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    routes = db.relationship('Route', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    cost_surfaces = db.relationship('CostSurface', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_ahp_weights(self):
        """Get AHP weights as dictionary"""
        if self.ahp_weights:
            return json.loads(self.ahp_weights)
        return None
    
    def set_ahp_weights(self, weights_dict):
        """Set AHP weights from dictionary"""
        self.ahp_weights = json.dumps(weights_dict)

    def get_metadata(self):
        """Get metadata as dictionary"""
        if self.project_metadata:
            return json.loads(self.project_metadata)
        return None

    def set_metadata(self, metadata_dict):
        """Set metadata from dictionary"""
        self.project_metadata = json.dumps(metadata_dict)

    def __repr__(self):
        return f'<Project {self.name}>'


class Route(db.Model):
    """Optimized route model"""
    __tablename__ = 'routes'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # Route data (stored as GeoJSON)
    geometry = db.Column(db.Text, nullable=False)  # GeoJSON LineString
    
    # Route metrics
    total_length = db.Column(db.Float)  # meters
    total_cost = db.Column(db.Float)  # Accumulated cost from LCP
    estimated_towers = db.Column(db.Integer)
    
    # Engineering validation
    is_valid = db.Column(db.Boolean, default=False)
    validation_errors = db.Column(db.Text)  # JSON array of errors
    
    # Metadata
    algorithm = db.Column(db.String(50), default='dijkstra')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_geometry(self):
        """Get geometry as GeoJSON dict"""
        if self.geometry:
            return json.loads(self.geometry)
        return None
    
    def set_geometry(self, geojson_dict):
        """Set geometry from GeoJSON dict"""
        self.geometry = json.dumps(geojson_dict)
    
    def get_validation_errors(self):
        """Get validation errors as list"""
        if self.validation_errors:
            return json.loads(self.validation_errors)
        return []
    
    def set_validation_errors(self, errors_list):
        """Set validation errors from list"""
        self.validation_errors = json.dumps(errors_list)
    
    def __repr__(self):
        return f'<Route {self.id} for Project {self.project_id}>'


class CostSurface(db.Model):
    """Cost surface model for storing generated composite cost surfaces"""
    __tablename__ = 'cost_surfaces'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    
    # File path to the cost surface raster
    file_path = db.Column(db.String(500), nullable=False)
    
    # Metadata
    resolution = db.Column(db.Float)  # meters per pixel
    bounds = db.Column(db.Text)  # JSON: [min_lon, min_lat, max_lon, max_lat]
    crs = db.Column(db.String(50), default='EPSG:4326')
    
    # Layer contributions (JSON)
    layer_weights = db.Column(db.Text)  # JSON of weights used
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_bounds(self):
        """Get bounds as list"""
        if self.bounds:
            return json.loads(self.bounds)
        return None
    
    def set_bounds(self, bounds_list):
        """Set bounds from list"""
        self.bounds = json.dumps(bounds_list)
    
    def __repr__(self):
        return f'<CostSurface {self.id} for Project {self.project_id}>'

