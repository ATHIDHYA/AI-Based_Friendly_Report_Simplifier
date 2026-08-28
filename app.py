from flask import Flask
from config import Config
from database.models import db
from routes.upload_routes import upload_bp
from routes.report_routes import report_bp
from routes.patient_routes import patient_bp

import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Database Extension
db.init_app(app)

with app.app_context():
    db_dir = os.path.join(Config.BASE_DIR, "database")
    os.makedirs(db_dir, exist_ok=True)
    db.create_all()

# Register Blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(report_bp)
app.register_blueprint(patient_bp)

if __name__ == "__main__":
    app.run(debug=True)