from flask import Flask
from .extensions import ma
from .models import db
from .blueprints import customers_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.service_tickets import service_tickets_bp


def create_app(config_name: str) -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    config_map = {
        "development": "config.DevelopmentConfig",
        "DevelopmentConfig": "config.DevelopmentConfig",
    }
    app.config.from_object(config_map.get(config_name, config_name))
    
    ma.init_app(app)
    db.init_app(app)
    
    
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service-tickets')
    
    return app