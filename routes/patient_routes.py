from flask import Blueprint, render_template, request, redirect, jsonify, flash, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.models import db, Patient, MedicalReport, User

patient_bp = Blueprint("patient", __name__, url_prefix="/patients")


@patient_bp.route("/", methods=["GET"])
def list_patients():
    """Lists all registered patients in professional table format."""
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template("patients.html", patients=patients)


@patient_bp.route("/add", methods=["GET", "POST"])
def add_patient():
    """Adds a new patient to the database."""
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        age = request.form.get("age", type=int)
        gender = request.form.get("gender", "").strip()
        blood_group = request.form.get("blood_group", "").strip()
        contact_email = request.form.get("contact_email", "").strip()
        contact_phone = request.form.get("contact_phone", "").strip()

        if not full_name:
            return render_template("add_patient.html", error="Patient full name is required.")

        patient = Patient(
            full_name=full_name,
            age=age,
            gender=gender,
            blood_group=blood_group,
            contact_email=contact_email,
            contact_phone=contact_phone,
        )
        db.session.add(patient)
        db.session.commit()

        return redirect(url_for("patient.view_patient", patient_id=patient.id))

    return render_template("add_patient.html")


@patient_bp.route("/<int:patient_id>", methods=["GET"])
def view_patient(patient_id):
    """Displays detailed patient record and history of medical reports."""
    patient = db.get_or_404(Patient, patient_id)
    return render_template("patient_detail.html", patient=patient)


@patient_bp.route("/api/list", methods=["GET"])
def api_list_patients():
    """Returns JSON list of patients for frontend select inputs."""
    patients = Patient.query.order_by(Patient.full_name.asc()).all()
    return jsonify([p.to_dict() for p in patients])


# API Routes for React frontend
@patient_bp.route("/api/list", methods=["GET"])
@jwt_required()
def api_get_patients():
    """API endpoint to get all patients as JSON"""
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return jsonify([p.to_dict() for p in patients])


@patient_bp.route("/api/<int:patient_id>", methods=["GET"])
@jwt_required()
def api_get_patient(patient_id):
    """API endpoint to get a specific patient as JSON"""
    patient = Patient.query.get_or_404(patient_id)
    patient_dict = patient.to_dict()
    
    # Include reports with their details
    patient_dict["reports"] = [report.to_dict() for report in patient.reports]
    
    return jsonify(patient_dict)


@patient_bp.route("/api", methods=["POST"])
@jwt_required()
def api_create_patient():
    """API endpoint to create a new patient"""
    data = request.get_json()
    
    if not data or not data.get("full_name"):
        return jsonify({"error": "Patient full name is required"}), 400
    
    patient = Patient(
        full_name=data.get("full_name"),
        age=data.get("age"),
        gender=data.get("gender"),
        blood_group=data.get("blood_group"),
        contact_email=data.get("contact_email"),
        contact_phone=data.get("contact_phone"),
    )
    
    try:
        db.session.add(patient)
        db.session.commit()
        return jsonify(patient.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to create patient: {str(e)}"}), 500


@patient_bp.route("/api/<int:patient_id>", methods=["PUT"])
@jwt_required()
def api_update_patient(patient_id):
    """API endpoint to update a patient"""
    patient = Patient.query.get_or_404(patient_id)
    data = request.get_json()
    
    try:
        if "full_name" in data:
            patient.full_name = data["full_name"]
        if "age" in data:
            patient.age = data["age"]
        if "gender" in data:
            patient.gender = data["gender"]
        if "blood_group" in data:
            patient.blood_group = data["blood_group"]
        if "contact_email" in data:
            patient.contact_email = data["contact_email"]
        if "contact_phone" in data:
            patient.contact_phone = data["contact_phone"]
        
        db.session.commit()
        return jsonify(patient.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to update patient: {str(e)}"}), 500


@patient_bp.route("/api/<int:patient_id>", methods=["DELETE"])
@jwt_required()
def api_delete_patient(patient_id):
    """API endpoint to delete a patient"""
    patient = Patient.query.get_or_404(patient_id)
    
    try:
        db.session.delete(patient)
        db.session.commit()
        return jsonify({"message": "Patient deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete patient: {str(e)}"}), 500
