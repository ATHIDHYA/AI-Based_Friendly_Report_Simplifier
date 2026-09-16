from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from database.models import db
from routes.upload_routes import upload_bp
from routes.report_routes import report_bp
from routes.patient_routes import patient_bp
from routes.auth_routes import auth_bp

import os

app = Flask(__name__)
app.config.from_object(Config)

# Configure JWT
app.config["JWT_SECRET_KEY"] = Config.SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False  # Use custom expiration in routes

# Initialize extensions
CORS(app)  # Enable CORS for React frontend
jwt = JWTManager(app)
db.init_app(app)

with app.app_context():
    db_dir = os.path.join(Config.BASE_DIR, "database")
    os.makedirs(db_dir, exist_ok=True)
    db.create_all()

# Register Blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(report_bp)
app.register_blueprint(patient_bp)
app.register_blueprint(auth_bp)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)