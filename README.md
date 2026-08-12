# 🏦 Bank Loan Approval Predictor

A Machine Learning based web application that predicts whether a bank loan application is likely to be **Approved** or **Rejected** based on applicant information.

## 🚀 Features

- Loan approval prediction using Machine Learning
- Applicant email notification
- MongoDB database integration
- Application history
- Admin login and dashboard
- Approval and rejection analytics
- CSV and Excel export
- Responsive UI
- Dark/Light theme
- Application details page

## 🛠️ Technologies Used

- Python
- Flask
- Pandas
- Scikit-learn
- MongoDB Atlas
- HTML
- CSS
- JavaScript
- Git & GitHub
- Vercel

## 📊 Machine Learning

The application uses a trained Machine Learning model to predict the loan status based on:

- Gender
- Married
- Dependents
- Education
- Self Employed
- Applicant Income
- Coapplicant Income
- Loan Amount
- Loan Amount Term
- Credit History
- Property Area

## 📁 Project Structure

```text
Bank-Loan-Approval-Predictor/
│
├── app.py
├── loan_model.pkl
├── requirements.txt
├── vercel.json
│
├── database/
│   └── mongodb.py
│
├── dataset/
│   └── loan_data.csv
│
├── static/
│   ├── style.css
│   └── theme.js
│
└── templates/
    ├── index.html
    ├── result.html
    ├── dashboard.html
    ├── history.html
    ├── analytics.html
    ├── export.html
    ├── admin_login.html
    ├── admin_dashboard.html
    └── ...
