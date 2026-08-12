from pymongo import MongoClient

MONGO_URI = "mongodb+srv://bankloan_user:Gaurav060501@bankloancluster.lphkltd.mongodb.net/?appName=BankLoanCluster"

client = MongoClient(MONGO_URI)

db = client["BankLoanDB"]

applications_collection = db["loan_applications"]

print("MongoDB connected successfully!")