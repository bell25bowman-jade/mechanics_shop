from app.__init__ import create_app
from app.models import db



app = create_app("ProductionConfig")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run()
