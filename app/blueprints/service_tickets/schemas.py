from app.extensions import ma
from app.models import Service


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Service
        include_relationships = True
        load_instance = True