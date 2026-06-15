from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DATE
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

service_inventory = db.Table(
    'service_inventory',
    db.Column('service_id', db.ForeignKey('services.id'), primary_key=True),
    db.Column('inventory_id', db.ForeignKey('inventory.id'), primary_key=True),
)

service_mechanic = db.Table(
    'service_mechanic',
    db.Column('service_id', db.ForeignKey('services.id'), primary_key=True),
    db.Column('mechanic_id', db.ForeignKey('mechanics.id'), primary_key=True),
)



class Mechanic(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(db.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)

    services: Mapped[list['Service']] = relationship(back_populates='mechanic')
    service_tickets: Mapped[list['Service']] = relationship(
        secondary=service_mechanic,
        back_populates='mechanics',
    )
    
class Customer(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(db.String(255), nullable=False)
    make_model: Mapped[str] = mapped_column(db.String(255), nullable=False)
    date: Mapped[DATE] = mapped_column(DATE)

    services: Mapped[list['Service']] = relationship(back_populates='customer')
    
class Service(Base):
    __tablename__ = 'services'

    id: Mapped[int] = mapped_column(primary_key=True)
    mechanic_id: Mapped[Optional[int]] = mapped_column(db.ForeignKey('mechanics.id'), nullable=True)
    customer_id: Mapped[int] = mapped_column(db.ForeignKey('customers.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(db.String(500), nullable=True)

    mechanic: Mapped[Optional['Mechanic']] = relationship(back_populates='services')
    customer: Mapped['Customer'] = relationship(back_populates='services')
    mechanics: Mapped[list['Mechanic']] = relationship(
        secondary=service_mechanic,
        back_populates='service_tickets',
    )
    inventory_items: Mapped[list['Inventory']] = relationship(
        secondary=service_inventory,
        back_populates='service_tickets',
    )


class Inventory(Base):
    __tablename__ = 'inventory'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    price: Mapped[float] = mapped_column(db.Float, nullable=False)

    service_tickets: Mapped[list['Service']] = relationship(
        secondary=service_inventory,
        back_populates='inventory_items',
    )