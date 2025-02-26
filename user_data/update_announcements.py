from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get MongoDB URI from environment variable
Mongo_uri = os.getenv('Mongo_uri')

client = MongoClient(Mongo_uri)
db = client.users_data
announcements_collection = db.announcements

# Update existing announcements to include a timestamp if missing
announcements = announcements_collection.find({'timestamp': {'$exists': False}})
for announcement in announcements:
    announcements_collection.update_one(
        {'_id': announcement['_id']},
        {'$set': {'timestamp': datetime.now()}}
    )

print("Updated announcements to include timestamp.")