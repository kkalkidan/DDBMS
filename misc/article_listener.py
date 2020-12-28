import pymongo
from pymongo import MongoClient
import time

client = MongoClient('mongodb://localhost:26000/')
db = client.db

with db.article.watch([{'$match': {'fullDocument.category': 'science'}}]) as stream:
    print("Connected to " + str(db))
    print("Listener started......")
    for change in stream:
        print("Document detected in Article ", change['fullDocument'])
        db.article.aggregate([
            {'$match': {"category": "science"}},
            {'$merge': {"into": "articlesci", "whenMatched":"replace"}}
        ])
        print("Updated in articlesci")