import pandas as pd
import numpy as np

np.random.seed(42)

rows = 1000

data = {
    "Gender": np.random.choice(["Male", "Female"], rows),
    "Married": np.random.choice(["Yes", "No"], rows),
    "Dependents": np.random.choice(["0", "1", "2", "3+"], rows),
    "Education": np.random.choice(["Graduate", "Not Graduate"], rows),
    "Self_Employed": np.random.choice(["Yes", "No"], rows),
    "ApplicantIncome": np.random.randint(15000, 100000, rows),
    "CoapplicantIncome": np.random.randint(0, 50000, rows),
    "LoanAmount": np.random.randint(50000, 1000000, rows),
    "Loan_Amount_Term": np.random.choice([120, 180, 240, 300, 360], rows),
    "Credit_History": np.random.choice([0, 1], rows, p=[0.15, 0.85]),
    "Property_Area": np.random.choice(
        ["Urban", "Semiurban", "Rural"], rows
    )
}

df = pd.DataFrame(data)

# Total income
total_income = (
    df["ApplicantIncome"] +
    df["CoapplicantIncome"]
)

# Simple logic for generating target
score = (
    (df["Credit_History"] * 3) +
    (df["Education"] == "Graduate").astype(int) +
    (total_income > 50000).astype(int) +
    (df["LoanAmount"] < 600000).astype(int)
)

df["Loan_Status"] = np.where(score >= 3, "Y", "N")

# Save CSV
df.to_csv("dataset/loan_data.csv", index=False)

print("Dataset created successfully!")
print("Total rows:", len(df))
print("Total columns:", len(df.columns))
print("\nFirst 5 records:")
print(df.head())