"""
OpenShift Service Mesh Inventory Demo - Backend Configuration
Centralized configuration management for the Flask application
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class"""
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    TESTING = False
    
    # Database configuration
    DB_HOST = os.getenv('DB_HOST', 'postgres-service')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'inventory')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
    
    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0,
        'pool_size': 10
    }
    
    # Service Mesh and legacy service configuration
    LEGACY_SERVICE_URL = os.getenv('LEGACY_SERVICE_URL', 'http://legacy-service:8080')
    USE_MOCK_VALIDATION = os.getenv('USE_MOCK_VALIDATION', 'false').lower() == 'true'
    
    # API configuration
    API_TITLE = 'OpenShift Service Mesh Inventory API'
    API_VERSION = '1.0.0'
    API_DESCRIPTION = 'Inventory management API demonstrating Service Mesh integration'
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Request timeout settings
    LEGACY_SERVICE_TIMEOUT = int(os.getenv('LEGACY_SERVICE_TIMEOUT', '10'))
    
    # CORS configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Health check configuration
    HEALTH_CHECK_TIMEOUT = 5
    
    # Rate limiting (if implemented)
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    
    # Service Mesh headers
    SERVICE_MESH_HEADERS = {
        'X-Service-Mesh': 'true',
        'X-Service-Name': 'inventory-backend',
        'X-Service-Version': '1.0.0'
    }


class DevelopmentConfig(Config):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'
    
    # Use SQLite for local development if no PostgreSQL
    if not Config.DB_HOST or Config.DB_HOST == 'localhost':
        SQLALCHEMY_DATABASE_URI = 'sqlite:///inventory_dev.db'


class TestingConfig(Config):
    """Testing environment configuration"""
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Use mock validation for testing
    USE_MOCK_VALIDATION = True


class ProductionConfig(Config):
    """Production environment configuration"""
    DEBUG = False
    TESTING = False
    
    # Require secret key in production
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set in production")
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Production database settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 20,
        'pool_size': 20
    }


class OpenShiftConfig(Config):
    """OpenShift specific configuration"""
    DEBUG = False
    TESTING = False
    
    # OpenShift environment detection
    OPENSHIFT_BUILD_NAME = os.getenv('OPENSHIFT_BUILD_NAME')
    OPENSHIFT_BUILD_NAMESPACE = os.getenv('OPENSHIFT_BUILD_NAMESPACE')
    
    # Service Mesh specific settings
    ISTIO_PROXY_CONFIG = {
        'proxyStatsMatcher': {
            'inclusionRegexps': [
                '.*circuit_breakers.*',
                '.*upstream_rq_retry.*',
                '.*_cx_.*'
            ]
        }
    }


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'openshift': OpenShiftConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'default').lower()
    
    # Auto-detect OpenShift environment
    if os.getenv('OPENSHIFT_BUILD_NAME') or os.getenv('KUBERNETES_SERVICE_HOST'):
        env = 'openshift'
    
    return config.get(env, config['default'])


# Environment-specific settings
class DatabaseConfig:
    """Database specific configuration and utilities"""
    
    @staticmethod
    def get_connection_url():
        """Get database connection URL with proper escaping"""
        config_class = get_config()
        return config_class.SQLALCHEMY_DATABASE_URI
    
    @staticmethod
    def is_postgresql():
        """Check if using PostgreSQL"""
        return get_config().SQLALCHEMY_DATABASE_URI.startswith('postgresql://')
    
    @staticmethod
    def is_sqlite():
        """Check if using SQLite"""
        return get_config().SQLALCHEMY_DATABASE_URI.startswith('sqlite://')


class ServiceMeshConfig:
    """Service Mesh specific configuration"""
    
    @staticmethod
    def get_mesh_headers():
        """Get headers for Service Mesh identification"""
        return get_config().SERVICE_MESH_HEADERS
    
    @staticmethod
    def is_mock_validation():
        """Check if using mock validation"""
        return get_config().USE_MOCK_VALIDATION
    
    @staticmethod
    def get_legacy_service_url():
        """Get legacy service URL"""
        return get_config().LEGACY_SERVICE_URL


# Application metadata
APP_METADATA = {
    'name': 'inventory-backend',
    'version': '1.0.0',
    'description': 'OpenShift Service Mesh Inventory Demo Backend',
    'author': 'OpenShift Demo Team',
    'repository': 'https://github.com/your-org/openshift-servicemesh-inventory-demo',
    'service_mesh': {
        'enabled': True,
        'version': '2.6',
        'features': [
            'mTLS',
            'traffic_management',
            'observability',
            'security_policies'
        ]
    }
}