import json
import requests

from pymongo import MongoClient

import info
import teams_info

if __name__ == "__main__":
    client = MongoClient(info.mongoLink)
    db = client.stats_trax

    teams_info.addTeamsInfo(db)
