from pymongo import MongoClient

# Connect to the MongoDB server
client = MongoClient("mongodb+srv://sunil:Suniel07@cluster0.ebv5vfe.mongodb.net/users_data")

# Select the database and collection
db = client.users_data
users_collection = db.users

# Define sample user data to insert
sample_users = [
    {
        "name": "John Doe",
        "dob": "1990-01-01",
        "course": "Computer Science",
        "semester": "6",
        "cgpa": "3.5",
        "picture": None
    },
    {
        "name": "Jane Smith",
        "dob": "1992-02-02",
        "course": "Mathematics",
        "semester": "4",
        "cgpa": "3.8",
        "picture": None
    },
    {
        "name": "Alice Johnson",
        "dob": "1991-03-03",
        "course": "Physics",
        "semester": "8",
        "cgpa": "3.9",
        "picture": None
    },
    {
        "name": "Bob Brown",
        "dob": "1993-04-04",
        "course": "Chemistry",
        "semester": "2",
        "cgpa": "3.2",
        "picture": None
    }
]

# Insert the sample user data into the collection
users_collection.insert_many(sample_users)
print("Database populated with dummy user data.")