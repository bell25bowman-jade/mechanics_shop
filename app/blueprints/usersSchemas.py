from app.extensions import ma
from app.models import Customer
from marshmallow import fields
        
class CustomerSchema(ma.SQLAlchemyAutoSchema):
    name = fields.String(required=True)
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)
    make_model = fields.String(required=True)
    date = fields.Date(required=False, allow_none=True)

    class Meta:
        model = Customer
        include_relationships = True
        load_instance = True


login_schema = CustomerSchema(only=("email", "password"))