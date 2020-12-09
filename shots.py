import json
import requests
import datetime
import math

from pymongo import MongoClient

import constants

''' Adds the games from  to stats_trax.games'''
def addShots(db):
    # Get the info for each game
    gamesCollection = db.schedule.find()

    # Initialize the gamesInfo array
    gamesInfo = []
    # Iterate through the collection of games
    for gameResult in gamesCollection:
        gamesInfo.append(gameResult)

    # Iterate through all the games
    for gameInfo in gamesInfo:
        if gameInfo['id'] < 2019020950:
            print(gameInfo['id'])
            continue
        # Get the dict on the game based on the id
        game = requests.get(constants.getGameUrl(gameInfo['id'])).json()

        # Iterate through the plays of the game
        for play in game['liveData']['plays']['allPlays']:
            # Filter out plays that are not shots
            if not 'SHOT' in play['result']['eventTypeId'] and play['result']['eventTypeId'] != 'GOAL':
                continue
            # Skip if the coordinates are not given
            if play['coordinates'] is None:
                continue
            # Skip if the shotType is not specified (when event=GOAL or event=SHOT)
            if not 'secondaryType' in play['result']:
                if not '_SHOT' in play['result']['eventTypeId']:
                    print('Skipping shot (shotType missing): Game=' + str(gameInfo['id']) + ' - eventId=' + str(play['about']['eventIdx']))
                    continue
                shotType = None
            # Otherwise specify the shotType
            else:
                shotType = play['result']['secondaryType']

            # If gameWinningGoal, emptyNet or strength are not specified, set them as none
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

            # Based on the type of shot, shooterIndex is the position of the shooter
            if play['result']['eventTypeId'] == 'BLOCKED_SHOT':
                shooterIndex = 1
            else:
                shooterIndex = 0

            # If shootsCatches is specified, use the given value, otherwise, set it to None
            if 'shootsCatches' in game['gameData']['players']['ID' + str(play['players'][shooterIndex]['player']['id'])]:
                shootsCatches = game['gameData']['players']['ID' + str(play['players'][shooterIndex]['player']['id'])]['shootsCatches']
            else:
                shootsCatches = None 

            # Initialize coordinates variables to simplify code
            xCoord = play['coordinates']['x']
            yCoord = play['coordinates']['y']   

            # Create the shot dict
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
                'players': getPlayersFromShot(game, play), 
                'shot': {
                    'shotType': shotType,
                    'shotAngle': getShotAngle(xCoord, yCoord),
                    'shotAngleAdjusted': abs(getShotAngle(xCoord, yCoord)),
                    'shotDistance': math.sqrt((90 - xCoord)*(90 - xCoord) + yCoord*yCoord),
                    'zone': getZone(play['about']['period'], xCoord), 
                    'offWing': isOffWing(shootsCatches, xCoord, yCoord),
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

            # Find any existing shots in the database with the same id
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

''' Get the zone of the shot based on the period and x coordinate '''
def getZone(period, xCoord):
    # If the x coordinate is withing 25 of the center, it is in the neutral zone
    if abs(xCoord) < 25.0:
        return 'NEUTRAL'

    # For periods 1/3, a positive x coordinate indicates it is in the home zone
    if xCoord > 0:
        homeZone = True
    else:
        homeZone = False

    # For period 2, the zones are the opposite
    if period % 2 == 0:
        homeZone = not homeZone
    
    # Based on the homeZone, return HOME/AWAY
    if homeZone:
        return 'HOME'
    else:
        return 'AWAY'

''' Check whether the shot was on the offwing '''
def isOffWing(shoots, xCoord, yCoord):
    # Return true if they shoot right and the coordinates have the same sign
    if shoots == 'R' and (xCoord > 0) == (yCoord > 0):
        return True
    # Return true if they shoot left and the coordinates have opposite signs
    elif shoots == 'L' and (xCoord > 0) != (yCoord > 0):
        return True
    # Else return false
    else:
        return False

'''  '''
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
        # If the shootsCatches is specified, set it to the given value, else set it to None, 
        if 'shootsCatches' in gameDict['gameData']['players']['ID' + str(player['player']['id'])]:
            shootsCatches = gameDict['gameData']['players']['ID' + str(player['player']['id'])]['shootsCatches']
        else:
            shootsCatches = None 

        # Set the add to the player dict
        players[player['playerType']] = {
            'id': player['player']['id'],
            'name': player['player']['fullName'],
            'playerType': player['playerType'],
            'shootsCatches': shootsCatches
        }

    # Return players dict
    return players

def getShotAngle(xCoord, yCoord):
    if xCoord == 90:
        return 90
    return math.degrees(math.atan(yCoord / (90 - xCoord)))