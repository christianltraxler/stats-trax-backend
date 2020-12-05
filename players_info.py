import json
import requests

from pymongo import MongoClient

import constants

''' Adds all the active players to the stats_trax.players'''
def addPlayersInfo(db):
    # Get all the teams from the teams collection
    teams = db.teams.find()

    # Iterate through all the teams
    for team in teams:
        # Get the dictionary of the roster of the team
        teamResponse = requests.get(constants.getTeamRosterUrl(team['id']))
        teamRoster = teamResponse.json()
        teamRoster = teamRoster['teams'][0]

        # Iterate through all the players on the team
        for player in teamRoster['roster']['roster']:
            # Get the dictionary of the player info based on the id
            playerResponse = requests.get(constants.getPlayerInfoUrl(player['person']['id']))
            playerInfo = playerResponse.json()
            playerInfo = playerInfo['people'][0]

            # If there is a primaryNumber key use it, else use None
            if 'primaryNumber' in playerInfo:
                primaryNumber = playerInfo['primaryNumber']
            else:
                primaryNumber = None

            # Based on the info of the player, generate a dictionary 
            player = {
                'id': playerInfo['id'],
                'name': {
                    'fullName': playerInfo['fullName'],
                    'firstName': playerInfo['firstName'],
                    'lastName': playerInfo['lastName']
                },
                'primaryNumber': primaryNumber,
                'currentTeam': {
                    'id': team['id'],
                    'name': team['name'],
                    'teamName': team['teamName'],
                    'abbreviation': team['abbreviation']
                },
                'primaryPosition': {
                    'code': playerInfo['primaryPosition']['code'],
                    'name': playerInfo['primaryPosition']['name'],
                    'type': playerInfo['primaryPosition']['type'],
                    'abbreviation': playerInfo['primaryPosition']['abbreviation']
                },
                'height':  playerInfo['height'],
                'weight': playerInfo['weight'],
                'shootsCatches': playerInfo['shootsCatches'],
                'picture' : {
                    'link': constants.getPlayerPictureUrl(playerInfo['id'], team['abbreviation'])
                },
                'rosterStatus' : playerInfo['rosterStatus'],
                "active" : playerInfo['active'],
                'info': {
                    'birthDate': playerInfo['birthDate'],
                    'birthCity': playerInfo['birthCity'],
                    'birthCountry': playerInfo['birthCountry'],
                    'nationality': playerInfo['nationality']
                }
            }

            # Find any existing plauers in the database with the same id
            dbPlayer = db.players.find_one({'id': player['id']})
            # Removed the _id key to compare the new dictionary with the one from the collection
            if (dbPlayer != None):
                dbPlayer.pop('_id')

            # If the new and collection dictionaries are different
            if (dbPlayer != player):
                print('Resetting player: ' + player['name']['fullName'])
                # Delete the existing info from the collection
                db.players.delete_one({'id': player['id']})
                # Add the new info into the collection
                db.players.insert_one(player)
            else:
                print('Skipping player: ' + player['name']['fullName'])



