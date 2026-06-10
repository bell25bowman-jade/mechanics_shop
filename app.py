from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DATE, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from flask_marshmallow import Marshmallow
from marshmallow import ValidationError
from typing import Optional

class Base(DeclarativeBase):
    pass

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:812288@localhost/mechanicshop'

db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

class Mechanic(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(db.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)

    services: Mapped[list['Service']] = relationship(back_populates='mechanic')
    customers: Mapped[list['Customer']] = relationship(secondary='services', back_populates='mechanics')
    
class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    make_model: Mapped[str] = mapped_column(db.String(255), nullable=False)
    date: Mapped[DATE] = mapped_column(DATE)

    services: Mapped[list['Service']] = relationship(back_populates='customer')
    mechanics: Mapped[list['Mechanic']] = relationship(secondary='services', back_populates='customers')
    
class Service(Base):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(primary_key=True)
    mechanic_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('mechanics.id'), nullable=True)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'), nullable=False)

    mechanic: Mapped[Optional['Mechanic']] = relationship(back_populates='services')
    customer: Mapped['Customer'] = relationship(back_populates='services')
    
#========schemas========
class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        include_relationships = True
        load_instance = True
        
class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        include_relationships = True
        load_instance = True
        
#========create tables========

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Mechanics Shop API",
        "endpoints": {
            "GET /customers": "List customers",
            "POST /customers": "Create customer",
            "GET /customers/<id>": "Get one customer",
            "PUT /customers/<id>": "Update customer",
            "DELETE /customers/<id>": "Delete customer"
        }
    }), 200

@app.errorhandler(405)
def method_not_allowed(err):
    return jsonify({
        "error": "Method Not Allowed",
        "message": "Use the correct HTTP method for this URL.",
    }), 405

#=======CREATE CUSTOMER========
@app.route("/customers", methods=["POST"])
def create_customer():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    query = select(Customer).where(Customer.name == data.get("name"))
    existing_customer = db.session.execute(query).scalar_one_or_none()
    if existing_customer:
        return jsonify({"message": "Customer with this name already exists."}), 400

    customer_schema = CustomerSchema()
    try:
        new_customer = customer_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201

#======Get all customers========
@app.route("/customers", methods=["GET"])
def get_customers():
    query = select(Customer)
    customers = db.session.execute(query).scalars().all()
    customer_schema = CustomerSchema(many=True)
    return customer_schema.jsonify(customers, many=True), 200

#=====get customer by id========
@app.route("/customers/<int:id>", methods=["GET"])
def get_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    customer_schema = CustomerSchema()
    return customer_schema.jsonify(customer), 200

#=====update customer by id========
@app.route("/customers/<int:id>", methods=["PUT"])
def update_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    data = request.get_json()
    customer_schema = CustomerSchema()
    updated_customer = customer_schema.load(data, instance=customer, partial=True)
    db.session.commit()
    return customer_schema.jsonify(updated_customer), 200

#====delete customer by id========
@app.route("/customers/<int:id>", methods=["DELETE"])
def delete_customer(id: int):
    customer = db.session.get(Customer, id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully."}), 200

#======create routs for mechanics======
#======creates new mechanic========
@app.route("/mechanic", methods=["POST"])
@app.route("/mechanics", methods=["POST"])
def create_mechanic():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    query = select(Mechanic).where(Mechanic.name == data.get("name"))
    existing_mechanic = db.session.execute(query).scalar_one_or_none()
    if existing_mechanic:
        return jsonify({"message": "Mechanic with this name already exists."}), 400

    mechanic_schema = MechanicSchema()
    try:
        new_mechanic = mechanic_schema.load(data)
    except ValidationError as err:
        return jsonify(err.messages), 400

    db.session.add(new_mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(new_mechanic), 201

#=====get all mechanics========
@app.route("/mechanics", methods=["GET"])
def get_mechanics():
    query = select(Mechanic)
    mechanics = db.session.execute(query).scalars().all()
    mechanic_schema = MechanicSchema(many=True)
    return mechanic_schema.jsonify(mechanics, many=True), 200

#=====update mechanic by id========
@app.route("/mechanics/<int:id>", methods=["PUT"])
def update_mechanic(id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404
    data = request.get_json()
    mechanic_schema = MechanicSchema()
    updated_mechanic = mechanic_schema.load(data, instance=mechanic, partial=True)
    db.session.commit()
    return mechanic_schema.jsonify(updated_mechanic), 200

#====delete mechanic by id========
@app.route("/mechanics/<int:id>", methods=["DELETE"])
def delete_mechanic(id: int):
    mechanic = db.session.get(Mechanic, id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404
    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": "Mechanic deleted successfully."}), 200

#=====service routs========
#====create service ticket=====
@app.route("/services", methods=["POST"])
def create_service():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body is required."}), 400

    mechanic_id = data.get("mechanic_id")
    customer_id = data.get("customer_id")

    mechanic = db.session.get(Mechanic, mechanic_id)
    if mechanic is None:
        return jsonify({"message": "Mechanic not found."}), 404

    customer = db.session.get(Customer, customer_id)
    if customer is None:
        return jsonify({"message": "Customer not found."}), 404

    new_service = Service(mechanic=mechanic, customer=customer)
    db.session.add(new_service)
    db.session.commit()
    
    return jsonify({"message": "Service ticket created successfully."}), 201

#====update service ticket========
@app.route("/services/<int:id>", methods=["PUT"])
def update_service(id: int):
    service = db.session.get(Service, id)
    if service is None:
        return jsonify({"message": "Service ticket not found."}), 404

    data = request.get_json()
    mechanic_id = data.get("mechanic_id")
    customer_id = data.get("customer_id")

    if mechanic_id is not None:
        mechanic = db.session.get(Mechanic, mechanic_id)
        if mechanic is None:
            return jsonify({"message": "Mechanic not found."}), 404
        service.mechanic = mechanic

    if customer_id is not None:
        customer = db.session.get(Customer, customer_id)
        if customer is None:
            return jsonify({"message": "Customer not found."}), 404
        service.customer = customer

    db.session.commit()
    return jsonify({"message": "Service ticket updated successfully."}), 200


#====remove mechanic from service ticket========
@app.route("/services/<int:id>/remove-mechanic", methods=["PUT"])
def remove_mechanic_from_service(id: int):
    service = db.session.get(Service, id)
    if service is None:
        return jsonify({"message": "Service ticket not found."}), 404

    if service.mechanic is None:
        return jsonify({"message": "Service ticket already has no mechanic."}), 200

    service.mechanic = None
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Unable to remove mechanic. Ensure services.mechanic_id is nullable in the database schema."
        }), 400

    return jsonify({"message": "Mechanic removed from service ticket successfully."}), 200


with app.app_context():
    db.create_all()
    
app.run()

