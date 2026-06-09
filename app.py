from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DATE
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:812288@localhost/mechanicshop'

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

db.init_app(app)

class Mechanic(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(db.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)

    services: Mapped[list['Service']] = relationship(back_populates='mechanic')
    customers: Mapped[list['Customer']] = relationship(
        secondary='services',
        back_populates='mechanics'
    )
    
class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    make_model: Mapped[str] = mapped_column(db.String(255), nullable=False)
    date: Mapped[DATE] = mapped_column(DATE)

    services: Mapped[list['Service']] = relationship(back_populates='customer')
    mechanics: Mapped[list['Mechanic']] = relationship(
        secondary='services',
        back_populates='customers'
    )
    
class Service(Base):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(primary_key=True)
    mechanic_id: Mapped[int] = mapped_column(db.ForeignKey('mechanics.id'), nullable=False)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'), nullable=False)

    mechanic: Mapped['Mechanic'] = relationship(back_populates='services')
    customer: Mapped['Customer'] = relationship(back_populates='services')
    
    
with app.app_context():
    db.create_all()
    
app.run()

