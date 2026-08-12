from flask import Flask, render_template, request, send_file, session, redirect, url_for

import pandas as pd
import pickle
import os
import smtplib

from dotenv import load_dotenv

from io import BytesIO
from bson import ObjectId
from datetime import datetime, timedelta

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from database.mongodb import applications_collection

load_dotenv()

app = Flask(__name__)

app.secret_key = "bank-loan-admin-secret-key"


# ============================================================
# LOAD TRAINED ML MODEL
# ============================================================

with open("loan_model.pkl", "rb") as file:
    model = pickle.load(file)


# ============================================================
# EMAIL CONFIGURATION
# ============================================================

SENDER_EMAIL = os.getenv("MAIL_USERNAME")
SENDER_PASSWORD = os.getenv("MAIL_PASSWORD")


# ============================================================
# SEND LOAN PREDICTION EMAIL
# ============================================================

def send_prediction_email(receiver_email, prediction, probability):

    # Email configuration check
    if not SENDER_EMAIL or not SENDER_PASSWORD:

        print("Email configuration is missing.")
        return False

    try:

        # ----------------------------------------------------
        # Prediction Status
        # ----------------------------------------------------

        if prediction == "Y":

            status = "APPROVED"

            message = (
                "Congratulations! Your loan application "
                "has been predicted as APPROVED."
            )

        else:

            status = "REJECTED"

            message = (
                "Your loan application has been predicted "
                "as REJECTED."
            )


        # ----------------------------------------------------
        # Email Subject
        # ----------------------------------------------------

        subject = "Bank Loan Prediction Result"


        # ----------------------------------------------------
        # Email Body
        # ----------------------------------------------------

        body = f"""
Dear Applicant,

Your Bank Loan Prediction has been completed.

----------------------------------------
Loan Prediction Result
----------------------------------------

Prediction Result       : {status}
Prediction Confidence   : {probability}%

{message}

Thank you for using Bank Loan Approval Predictor.

Regards,
Bank Loan Approval Predictor
"""


        # ----------------------------------------------------
        # Create Email
        # ----------------------------------------------------

        msg = MIMEMultipart()

        msg["From"] = SENDER_EMAIL
        msg["To"] = receiver_email
        msg["Subject"] = subject

        msg.attach(
            MIMEText(body, "plain")
        )


        # ----------------------------------------------------
        # Gmail SMTP
        # ----------------------------------------------------

        with smtplib.SMTP(
            "smtp.gmail.com",
            587
        ) as server:

            server.starttls()

            server.login(
                SENDER_EMAIL,
                SENDER_PASSWORD
            )

            server.send_message(msg)


        print(
            f"Prediction email sent successfully to {receiver_email}"
        )

        return True


    except Exception as e:

        print(
            "Email sending failed:",
            e
        )

        return False


# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")


        # if username == "Gaurav" and password == "Gaurav96k":

        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if username == admin_username and password == admin_password:


            session["admin_logged_in"] = True

            return redirect(
                url_for("admin_dashboard")
            )


        return render_template(
            "admin_login.html",
            error="Invalid username or password"
        )


    return render_template(
        "admin_login.html"
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
def admin_dashboard():

    if not session.get("admin_logged_in"):

        return redirect(
            url_for("admin_login")
        )


    total_applications = (
        applications_collection.count_documents({})
    )


    approved_applications = (
        applications_collection.count_documents({
            "Loan_Status_Prediction": "Y"
        })
    )


    rejected_applications = (
        applications_collection.count_documents({
            "Loan_Status_Prediction": "N"
        })
    )


    return render_template(

        "admin_dashboard.html",

        total_applications=total_applications,

        approved_applications=approved_applications,

        rejected_applications=rejected_applications

    )


# ============================================================
# DELETE APPLICATION
# ============================================================

@app.route(
    "/admin/delete/<application_id>",
    methods=["POST"]
)
def admin_delete_application(application_id):

    if not session.get("admin_logged_in"):

        return redirect(
            url_for("admin_login")
        )


    try:

        applications_collection.delete_one({
            "_id": ObjectId(application_id)
        })


    except Exception:

        return "Invalid Application ID", 400


    return redirect(
        url_for("admin_applications")
    )


# ============================================================
# DELETE ALL APPLICATIONS
# ============================================================

@app.route(
    "/admin/delete-all",
    methods=["POST"]
)
def admin_delete_all():

    if not session.get("admin_logged_in"):

        return redirect(
            url_for("admin_login")
        )


    try:

        applications_collection.delete_many({})

        return redirect(
            url_for("admin_applications")
        )


    except Exception as e:

        return (
            f"Error deleting applications: {e}",
            500
        )


# ============================================================
# ADMIN APPLICATIONS
# ============================================================

@app.route("/admin/applications")
def admin_applications():

    if not session.get("admin_logged_in"):

        return redirect(
            url_for("admin_login")
        )


    applications = list(
        applications_collection.find({}).sort(
            "Application_Date",
            -1
        )
    )


    return render_template(

        "admin_applications.html",

        applications=applications

    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

@app.route("/admin/logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )


    return redirect(
        url_for("admin_login")
    )


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    total_applications = (
        applications_collection.count_documents({})
    )


    approved_applications = (
        applications_collection.count_documents({
            "Loan_Status_Prediction": "Y"
        })
    )


    rejected_applications = (
        applications_collection.count_documents({
            "Loan_Status_Prediction": "N"
        })
    )


    # --------------------------------------------------------
    # Approval Rate
    # --------------------------------------------------------

    if total_applications > 0:

        approval_rate = round(
            (
                approved_applications
                / total_applications
            ) * 100,
            2
        )

    else:

        approval_rate = 0


    # --------------------------------------------------------
    # Average Income
    # --------------------------------------------------------

    income_result = list(
        applications_collection.aggregate([

            {
                "$group": {

                    "_id": None,

                    "average_income": {
                        "$avg": "$ApplicantIncome"
                    }

                }
            }

        ])
    )


    average_income = (

        round(
            income_result[0]["average_income"],
            2
        )

        if income_result

        else 0

    )


    # --------------------------------------------------------
    # Average Loan Amount
    # --------------------------------------------------------

    loan_result = list(
        applications_collection.aggregate([

            {
                "$group": {

                    "_id": None,

                    "average_loan": {
                        "$avg": "$LoanAmount"
                    }

                }
            }

        ])
    )


    average_loan_amount = (

        round(
            loan_result[0]["average_loan"],
            2
        )

        if loan_result

        else 0

    )


    # --------------------------------------------------------
    # Last 7 Days Analytics
    # --------------------------------------------------------

    today = datetime.now().date()

    analytics_labels = []
    analytics_approved = []
    analytics_rejected = []


    for i in range(6, -1, -1):

        current_date = (
            today - timedelta(days=i)
        )

        next_date = (
            current_date + timedelta(days=1)
        )


        start_datetime = datetime.combine(
            current_date,
            datetime.min.time()
        )


        end_datetime = datetime.combine(
            next_date,
            datetime.min.time()
        )


        approved_count = (
            applications_collection.count_documents({

                "Loan_Status_Prediction": "Y",

                "Application_Date": {

                    "$gte": start_datetime,

                    "$lt": end_datetime

                }

            })
        )


        rejected_count = (
            applications_collection.count_documents({

                "Loan_Status_Prediction": "N",

                "Application_Date": {

                    "$gte": start_datetime,

                    "$lt": end_datetime

                }

            })
        )


        analytics_labels.append(
            current_date.strftime("%d %b")
        )


        analytics_approved.append(
            approved_count
        )


        analytics_rejected.append(
            rejected_count
        )


    return render_template(

        "index.html",

        total_applications=total_applications,

        approved_applications=approved_applications,

        rejected_applications=rejected_applications,

        approval_rate=approval_rate,

        average_income=average_income,

        average_loan_amount=average_loan_amount,

        analytics_labels=analytics_labels,

        analytics_approved=analytics_approved,

        analytics_rejected=analytics_rejected

    )


# ============================================================
# LOAN PREDICTION
# ============================================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    # --------------------------------------------------------
    # Get Applicant Email
    # --------------------------------------------------------

    applicant_email = request.form.get(
        "Email"
    )


    if not applicant_email:

        return (
            "Email address is required.",
            400
        )


    # --------------------------------------------------------
    # Get Data From HTML Form
    # --------------------------------------------------------

    data = {

        "Email": applicant_email,

        "Gender": request.form["Gender"],

        "Married": request.form["Married"],

        "Dependents": request.form["Dependents"],

        "Education": request.form["Education"],

        "Self_Employed": request.form["Self_Employed"],

        "ApplicantIncome": int(
            request.form["ApplicantIncome"]
        ),

        "CoapplicantIncome": int(
            request.form["CoapplicantIncome"]
        ),

        "LoanAmount": int(
            request.form["LoanAmount"]
        ),

        "Loan_Amount_Term": int(
            request.form["Loan_Amount_Term"]
        ),

        "Credit_History": int(
            request.form["Credit_History"]
        ),

        "Property_Area": request.form["Property_Area"]

    }


    # --------------------------------------------------------
    # Convert Data Into DataFrame
    # --------------------------------------------------------

    input_data = pd.DataFrame([data])


    # --------------------------------------------------------
    # Remove Email Before ML Prediction
    # --------------------------------------------------------

    model_input = input_data.drop(
        columns=["Email"]
    )


    # --------------------------------------------------------
    # Make Prediction
    # --------------------------------------------------------

    prediction = model.predict(
        model_input
    )[0]


    probability = model.predict_proba(
        model_input
    )[0]


    # --------------------------------------------------------
    # Calculate Prediction Confidence
    # --------------------------------------------------------

    if prediction == "Y":

        probability_percent = round(
            probability[1] * 100,
            2
        )

    else:

        probability_percent = round(
            probability[0] * 100,
            2
        )


    # --------------------------------------------------------
    # Save Application In MongoDB
    # --------------------------------------------------------

    data["Application_Date"] = datetime.now()

    data["Loan_Status_Prediction"] = prediction

    data["Prediction_Confidence"] = (
        probability_percent
    )


    applications_collection.insert_one(
        data
    )


    # --------------------------------------------------------
    # SEND EMAIL NOTIFICATION
    # --------------------------------------------------------

    email_sent = send_prediction_email(

        applicant_email,

        prediction,

        probability_percent

    )


    # --------------------------------------------------------
    # Show Result
    # --------------------------------------------------------

    return render_template(

        "result.html",

        prediction=prediction,

        probability=probability_percent,

        email_sent=email_sent

    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():

    total_applications = (
        applications_collection.count_documents({})
    )


    approved_applications = (
        applications_collection.count_documents({

            "Loan_Status_Prediction": "Y"

        })
    )


    rejected_applications = (
        applications_collection.count_documents({

            "Loan_Status_Prediction": "N"

        })
    )


    # --------------------------------------------------------
    # Approval Rate
    # --------------------------------------------------------

    if total_applications > 0:

        approval_rate = round(

            (
                approved_applications
                / total_applications
            ) * 100,

            2

        )

    else:

        approval_rate = 0


    # --------------------------------------------------------
    # Average Applicant Income
    # --------------------------------------------------------

    income_result = list(
        applications_collection.aggregate([

            {
                "$group": {

                    "_id": None,

                    "average_income": {
                        "$avg": "$ApplicantIncome"
                    }

                }
            }

        ])
    )


    if income_result:

        average_income = round(

            income_result[0]["average_income"],

            2

        )

    else:

        average_income = 0


    # --------------------------------------------------------
    # Average Loan Amount
    # --------------------------------------------------------

    loan_result = list(
        applications_collection.aggregate([

            {
                "$group": {

                    "_id": None,

                    "average_loan": {
                        "$avg": "$LoanAmount"
                    }

                }
            }

        ])
    )


    if loan_result:

        average_loan_amount = round(

            loan_result[0]["average_loan"],

            2

        )

    else:

        average_loan_amount = 0


    return render_template(

        "dashboard.html",

        total_applications=total_applications,

        approved_applications=approved_applications,

        rejected_applications=rejected_applications,

        approval_rate=approval_rate,

        average_income=average_income,

        average_loan_amount=average_loan_amount

    )


# ============================================================
# APPLICATION HISTORY
# ============================================================

@app.route("/history")
def history():

    status = request.args.get(
        "status",
        "all"
    )


    # --------------------------------------------------------
    # Approved Applications
    # --------------------------------------------------------

    if status == "approved":

        applications = list(

            applications_collection.find({

                "Loan_Status_Prediction": "Y"

            }).sort(

                "Application_Date",
                -1

            )

        )


        page_title = "Approved Applications"

        page_description = (
            "Applications predicted as approved"
        )


    # --------------------------------------------------------
    # Rejected Applications
    # --------------------------------------------------------

    elif status == "rejected":

        applications = list(

            applications_collection.find({

                "Loan_Status_Prediction": "N"

            }).sort(

                "Application_Date",
                -1

            )

        )


        page_title = "Rejected Applications"

        page_description = (
            "Applications predicted as rejected"
        )


    # --------------------------------------------------------
    # All Applications
    # --------------------------------------------------------

    else:

        applications = list(

            applications_collection.find({}).sort(

                "Application_Date",
                -1

            )

        )


        page_title = "Application History"

        page_description = (
            "All previous loan prediction applications"
        )


    return render_template(

        "history.html",

        applications=applications,

        page_title=page_title,

        page_description=page_description

    )


# ============================================================
# APPLICATION DETAILS
# ============================================================

@app.route(
    "/application/<application_id>"
)
def application_details(application_id):

    try:

        application = (
            applications_collection.find_one({

                "_id": ObjectId(application_id)

            })
        )


    except Exception:

        return (
            "Invalid Application ID",
            404
        )


    if application is None:

        return (
            "Application not found",
            404
        )


    return render_template(

        "application_details.html",

        application=application

    )


# ============================================================
# ANALYTICS
# ============================================================

@app.route("/analytics")
def analytics():

    # --------------------------------------------------------
    # Total Application Overview
    # --------------------------------------------------------

    approved_count = (
        applications_collection.count_documents({

            "Loan_Status_Prediction": "Y"

        })
    )


    rejected_count = (
        applications_collection.count_documents({

            "Loan_Status_Prediction": "N"

        })
    )


    # --------------------------------------------------------
    # Last 7 Days Analytics
    # --------------------------------------------------------

    today = datetime.now().date()

    analytics_labels = []
    analytics_approved = []
    analytics_rejected = []


    for i in range(6, -1, -1):

        current_date = (
            today - timedelta(days=i)
        )

        next_date = (
            current_date + timedelta(days=1)
        )


        start_datetime = datetime.combine(

            current_date,

            datetime.min.time()

        )


        end_datetime = datetime.combine(

            next_date,

            datetime.min.time()

        )


        # Approved

        approved = (
            applications_collection.count_documents({

                "Loan_Status_Prediction": "Y",

                "Application_Date": {

                    "$gte": start_datetime,

                    "$lt": end_datetime

                }

            })
        )


        # Rejected

        rejected = (
            applications_collection.count_documents({

                "Loan_Status_Prediction": "N",

                "Application_Date": {

                    "$gte": start_datetime,

                    "$lt": end_datetime

                }

            })
        )


        analytics_labels.append(

            current_date.strftime("%d %b")

        )


        analytics_approved.append(
            approved
        )


        analytics_rejected.append(
            rejected
        )


    return render_template(

        "analytics.html",

        approved_count=approved_count,

        rejected_count=rejected_count,

        analytics_labels=analytics_labels,

        analytics_approved=analytics_approved,

        analytics_rejected=analytics_rejected

    )


# ============================================================
# EXPORT PAGE
# ============================================================

@app.route("/export")
def export_page():

    return render_template(
        "export.html"
    )


# ============================================================
# EXPORT CSV
# ============================================================

@app.route("/export/csv")
def export_csv():

    applications = list(

        applications_collection.find(

            {},

            {
                "_id": 0
            }

        )

    )


    if not applications:

        return (
            "No applications available for export."
        )


    df = pd.DataFrame(
        applications
    )


    output = BytesIO()


    csv_data = df.to_csv(
        index=False
    )


    output.write(
        csv_data.encode("utf-8")
    )


    output.seek(0)


    return send_file(

        output,

        mimetype="text/csv",

        as_attachment=True,

        download_name="loan_applications.csv"

    )


# ============================================================
# EXPORT EXCEL
# ============================================================

@app.route("/export/excel")
def export_excel():

    applications = list(

        applications_collection.find(

            {},

            {
                "_id": 0
            }

        )

    )


    if not applications:

        return (
            "No applications available for export."
        )


    df = pd.DataFrame(
        applications
    )


    output = BytesIO()


    with pd.ExcelWriter(

        output,

        engine="openpyxl"

    ) as writer:

        df.to_excel(

            writer,

            index=False,

            sheet_name="Applications"

        )


    output.seek(0)


    return send_file(

        output,

        mimetype=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),

        as_attachment=True,

        download_name="loan_applications.xlsx"

    )


# ============================================================
# ERROR HANDLING - 404
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "404.html"
    ), 404


# ============================================================
# ERROR HANDLING - 500
# ============================================================

@app.errorhandler(500)
def internal_server_error(error):

    return render_template(
        "500.html"
    ), 500


# ============================================================
# RUN FLASK APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(debug=True)