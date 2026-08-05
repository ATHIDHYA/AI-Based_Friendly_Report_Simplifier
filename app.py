from flask import Flask
from config import Config

from routes.upload_routes import upload_bp
from routes.report_routes import report_bp

app = Flask(__name__)
app.config.from_object(Config)

# Register Blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(report_bp)

if __name__ == "__main__":
    app.run(debug=True)