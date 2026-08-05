from flask import Blueprint, render_template, request, current_app
from werkzeug.utils import secure_filename
import os

from core.extractor import extract_text
from core.simplifier import simplify_report

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@upload_bp.route("/upload", methods=["POST"])
def upload():

    file = request.files.get("report")
    report_text = request.form.get("report_text", "").strip()

    text = ""

    # -----------------------------
    # Case 1 : User uploaded a file
    # -----------------------------
    if file and file.filename != "":

        filename = secure_filename(file.filename)

        upload_folder = current_app.config["UPLOAD_FOLDER"]

        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, filename)

        file.save(filepath)

        extracted = extract_text(filepath)

        text = extracted["text"]

    # -----------------------------
    # Case 2 : User pasted text
    # -----------------------------
    elif report_text:

        text = report_text

    # -----------------------------
    # Nothing supplied
    # -----------------------------
    else:

        return render_template(
            "index.html",
            error="Please upload a PDF/Image or paste report text."
        )

    # Run AI pipeline
    result = simplify_report(text)

    return render_template(
        "results.html",
        result=result
    )