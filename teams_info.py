import json
import requests

from pymongo import MongoClient

import constants

''' Adds all the active teams to the stats_trax.teams'''
def addTeamsInfo(db):
    # Get the dictionary of the info of all the active teams
    teamsDict = requests.get(constants.getAllTeamsInfoUrl()).json()['teams']

    # Iterate through all the teams 
    # For each team, either add it to the dictionary or skip if it already exists
    for teamInfo in teamsDict:
        # Based on the info of the team, generate a dictionary 
        team = {
            'id': teamInfo['id'],
            'name': teamInfo['name'],
            'abbreviation': teamInfo['abbreviation'],
            'teamName': teamInfo['teamName'],
            'locationName': teamInfo['locationName'],
            'logo' : {
                'link': constants.getTeamLogoUrl(teamInfo['abbreviation'])
            },
            'division' : {
                'id' : teamInfo['division']['id'],
                'name' : teamInfo['division']['name']
            },
            'conference' : {
                'id' : teamInfo['conference']['id'],
                'name' : teamInfo['conference']['name']
            },
            'city': teamInfo['venue']['city'],
            'shortName': teamInfo['shortName'],
            'franchiseId': teamInfo['franchiseId'],
            'active': teamInfo['active']
        }

        # Find any existing teams in the database with the same id
        dbTeam = db.teams.find_one({'id': teamInfo['id']})
        # Removed the _id key to compare the new dictionary with the one from the collection
        if (dbTeam != None):
            dbTeam.pop('_id')

        # If the new and collection dictionaries are different
        if (dbTeam != team):
            print('Resetting team: ' + team['name'])
            # Delete the existing info from the collection
            db.teams.delete_one({'id': teamInfo['id']})
            # Add the new info into the collection
            db.teams.insert_one(team)
        else:
            print('Skipping team: ' + team['name'])
