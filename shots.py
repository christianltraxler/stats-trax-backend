import json
import requests
import datetime
import math

from pymongo import MongoClient

import constants

''' Adds the games from  to stats_trax.games'''
def addShots(db):
    # Get the info for each game
    gamesInfo = db.schedule.find()

    for gameInfo in gamesInfo:
        game = requests.get(constants.getGameUrl(gameInfo['id'])).json()

        for play in game['liveData']['plays']['allPlays']:
            if not 'team' in play or not 'players' in play:
                continue
            if not 'SHOT' in play['result']['eventTypeId'] and play['result']['eventTypeId'] != 'GOAL':
                continue
            if play['coordinates'] is None:
                continue
            
            if not 'secondaryType' in play['result']:
                if not '_SHOT' in play['result']['eventTypeId']:
                    print('Skipping shot (shotType missing): Game=' + str(gameInfo['id']) + ' - eventId=' + str(play['about']['eventIdx']))
                    continue
                shotType = None
            else:
                shotType = play['result']['secondaryType']

            if 'gameWinningGoal' in play:
                gameWinningGoal = play['result']['gameWinningGoal']
            else:
                gameWinningGoal = None
            if 'emptyNet' in play:
                emptyNet = play['result']['emptyNet']
            else:
                emptyNet = None
            if 'strength' in play['result']:
                strength = play['result']['strength']
            else:
                strength = None

            shootsCatches = game['gameData']['players']['ID' + str(play['players'][0]['player']['id'])]['shootsCatches']
            xCoord = play['coordinates']['x']
            yCoord = play['coordinates']['y']   
            shot = {
                'gameId': gameInfo['id'],
                'gameType': gameInfo['gameType'], 
                'season': gameInfo['season'], 
                'eventId': play['about']['eventIdx'],
                'eventType': play['result']['eventTypeId'],
                'about': {
                    'period': play['about']['period'], 
                    'periodType': play['about']['periodType'],
                    'periodTime': play['about']['periodTime'],
                    'periodTimeRemaining': play['about']['periodTimeRemaining'],
                },
                'players': getPlayersFromShot(game, play), # Fix method to use new game
                'shot': {
                    'shotType': shotType,
                    'shotAngle': getShotAngle(xCoord, yCoord),
                    'shotAngleAdjusted': abs(getShotAngle(xCoord, yCoord)),
                    'shotDistance': math.sqrt((90 - xCoord)*(90 - xCoord) + yCoord*yCoord),
                    'zone': getZone(play['about']['period'], xCoord), 
                    'offWing': isOffWing(shootsCatches, yCoord),
                    'strength': strength,
                    'gameWinningGoal': gameWinningGoal,
                    'emptyNet': emptyNet       
                },
                'coordinates': {
                    'x': xCoord,
                    'y': yCoord,
                    'xAdjusted': abs(xCoord),
                    'yAdjusted': abs(yCoord)
                },
                'teams': getTeamsFromShot(game, play),
                'score': play['about']['goals']
            }

            # Find any existing games in the database with the same id
            dbShot = db.shots.find_one({'gameId': gameInfo['id'], 'eventId': play['about']['eventIdx']})

            # Removed the _id key to compare the new dictionary with the one from the collection
            if (dbShot != None):
                dbShot.pop('_id')

            # If the new and collection dictionaries are different
            if (dbShot != shot):
                print('Resetting shot: Game=' + str(gameInfo['id']) + ' - eventId=' + str(play['about']['eventIdx']))
                # Delete the existing info from the collection
                db.shots.delete_one({'gameId': gameInfo['id'], 'eventId': play['about']['eventIdx']})
                # Add the new info into the collection
                db.shots.insert_one(shot)
            else:
                print('Skipping shot: Game=' + str(gameInfo['id']) + ' - eventId=' + str(play['about']['eventIdx']))

def getZone(period, xCoord):
    if abs(xCoord) < 25.0:
        return 'NEUTRAL'

    if xCoord > 0:
        homeZone = True
    else:
        homeZone = False

    if period % 2 == 0:
        homeZone = not homeZone
    
    if homeZone:
        return 'HOME'
    else:
        return 'AWAY'

def isOffWing(shoots, yCoord):
    if (shoots == 'R' and abs(yCoord) > 0) or (shoots == 'L' and abs(yCoord < 0)):
        return True
    else:
        return False

def getTeamsFromShot(gameDict, play):

    # If the team specified in the play is the same as the home team
    if play['team']['id'] == gameDict['gameData']['teams']['home']['id']:
        # The play is for the home team
        homeOffenseDefense = True
    else: 
        # The play is against the home team
        homeOffenseDefense = False

    # Create the teams dict 
    teams = {
        'away': {
            'id': gameDict['gameData']['teams']['away']['id'],
            'name':gameDict['gameData']['teams']['away']['name'],
            'offenceDefence': not homeOffenseDefense
        },
        'home': {
            'id': gameDict['gameData']['teams']['home']['id'],
            'name': gameDict['gameData']['teams']['home']['name'],
            'offenseDefence': homeOffenseDefense
        }
    }
    return teams

def getPlayersFromShot(gameDict, play):

    # Initialize player dict
    players = {}

    # Iterate through the players
    for player in play['players']:

        # Set the add to the player dict
        players[player['playerType']] = {
            'id': player['player']['id'],
            'name': player['player']['fullName'],
            'playerType': player['playerType'],
            'shootsCatches': gameDict['gameData']['players']['ID' + str(player['player']['id'])]['shootsCatches']
        }

    # Return players dict
    return players

def getShotAngle(xCoord, yCoord):
    if xCoord == 90:
        return 90
    return math.degrees(math.atan(yCoord / (90 - xCoord)))