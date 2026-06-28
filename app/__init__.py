from flask import Flask, app
from .extensions import ma, cache, limiter
from .models import db
from .blueprints.customers import customers_bp
from .blueprints.mechanics import mechanics_bp
from .blueprints.service_tickets import service_tickets_bp
from .blueprints.inventory import inventory_bp
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = "/swagger"
API_URL = "/static/swagger.yaml"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "Service Ticket API"
    }
)

def create_app(config_name: str) -> Flask:
    app = Flask(__name__)
    app.register_blueprint(
        swaggerui_blueprint,
        url_prefix=SWAGGER_URL
    )
    app.url_map.strict_slashes = False
    config_map = {
        "development": "config.DevelopmentConfig",
        "DevelopmentConfig": "config.DevelopmentConfig",
        "testing": "config.TestingConfig",
        "TestingConfig": "config.TestingConfig",
        "production": "config.ProductionConfig",
        "ProductionConfig": "config.ProductionConfig",
    }
    app.config.from_object(config_map.get(config_name, config_name))
    
    ma.init_app(app)
    db.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service-tickets')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    
    return app


# Allow platforms configured with `gunicorn app:app` to load the WSGI app.
app = create_app("ProductionConfig")