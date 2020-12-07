import json
import requests
import datetime

from pymongo import MongoClient

import constants

''' Adds the games from the stats_trax.schedule collection to stats_trax.games'''
def addGames(db):
    # Retrieve the games from the stats_trax.schedule collection
    schedule = db.schedule.find()

    # Iterate through the games from the schedule
    for gameInfo in schedule:
        #Get the dictionary corresponding to the game specified
        gameDict = requests.get(constants.getGameUrl(gameInfo['id'])).json()

        # Create the game dictionary
        game = {
            'id': gameDict['gamePk'],
            'teams': {
                'away': {
                    'id': gameDict['liveData']['boxscore']['teams']['away']['team']['id'],
                    'name': gameDict['liveData']['boxscore']['teams']['away']['team']['name'],
                    'teamStats': gameDict['liveData']['boxscore']['teams']['away']['teamStats']
                },
                'home': {
                    'id': gameDict['liveData']['boxscore']['teams']['home']['team']['id'],
                    'name': gameDict['liveData']['boxscore']['teams']['home']['team']['name'],
                    'teamStats': gameDict['liveData']['boxscore']['teams']['home']['teamStats']
                }
            }
        }
        # Add the gameplayers to the game dictionary
        game.update(getGamePlayers(gameDict))
        # Add the game plays to the game dictionary
        game.update(getGamePlays(gameDict))

        # Find any existing games in the database with the same id
        dbGame = db.games.find_one({'id': gameInfo['id']})
        # Removed the _id key to compare the new dictionary with the one from the collection
        if (dbGame != None):
            dbGame.pop('_id')

        # If the new and collection dictionaries are different
        if (dbGame != game):
            print('Resetting game: ' + str(gameInfo['id']))
            # Delete the existing info from the collection
            db.games.delete_one({'id': gameInfo['id']})
            # Add the new info into the collection
            db.games.insert_one(game)
        else:
            print('Skipping game: ' + str(gameInfo['id']))

''''''
def getGamePlayers(gameDict):
    players = { 'players': {} }
    playersInfo = gameDict['liveData']['boxscore']['teams']['away']['players']
    playersInfo.update(gameDict['liveData']['boxscore']['teams']['home']['players'])
    
    for playerId in playersInfo:
        playerInfo = playersInfo[playerId]
        if 'skaterStats' in playerInfo['stats']:
            playerStats = playerInfo['stats']['skaterStats']
        elif 'goalieStats' in playerInfo['stats']:
            playerStats = playerInfo['stats']['goalieStats']
        else:
            playerStats = None
        
        if 'shootsCatches' in playerInfo['person']:
            shootsCatches = playerInfo['person']['shootsCatches']
        else:
            shootsCatches = None

        players['players'][str(playerInfo['person']['id'])] = {
            'id': playerInfo['person']['id'],
            'name': playerInfo['person']['fullName'],
            'position': {
                'code': playerInfo['position']['code'],
                'name': playerInfo['position']['name'],
                'type': playerInfo['position']['type']
            },
            'team': getTeamFromPlayerId(gameDict, playerInfo['person']['id']),
            'primaryNumber': playerInfo['jerseyNumber'],
            'shootsCatches': shootsCatches,
            'stats': playerStats
        }

    
    return players

''' Get plays from the game'''
def getGamePlays(gameDict):
    # Simplify gameDict to just the plays
    allPlays = gameDict['liveData']['plays']['allPlays']

    # Initialize playsArray to hold plays
    playsArray = []

    # Iterate through all the plays
    for play in allPlays:
        # If the play does not have the 'team' or 'players' key, skip play
        #       Skip uneccessary plays (ex: GAME_START, PERIOD_START, PERIOD_END, etc.)
        if not 'team' in play or not 'players' in play: 
            if play['result']['eventTypeId'] in ['PERIOD_START', 'STOP', 'PERIOD_END', 'SHOOTOUT_COMPLETE', 'CHALLENGE', 'EMERGENCY_GOALTENDER']:
                playDict = {
                    'eventId': play['about']['eventIdx'],
                    'eventType': play['result']['eventTypeId'],
                    'about': {
                        'period': play['about']['period'], 
                        'periodType': play['about']['periodType'],
                        'periodTime': play['about']['periodTime'],
                        'periodTimeRemaining': play['about']['periodTimeRemaining'],
                    },
                    'description': play['result']['description']
                }
                playsArray.append(playDict)
            continue

        # If the 'secondaryType' key exists; set the shotType, else empty
        if 'secondaryType' in play['result']:
            shotType = { 'shotType': play['result']['secondaryType'] }
        else:
            shotType = { 'shotType': None }

        # If the 'emptyNet' key exists; set emptyNet, else empty
        if 'emptyNet' in play['result']:
            emptyNet = play['result']['emptyNet'] 
        else:
            emptyNet = None

        # If the eventType is 'GOAL'; set goal dict, else empty
        if play['result']['eventTypeId'] == 'GOAL':
            if shotType is not None:
                goal = { 'goal': shotType }
                goal['goal'].update({
                        'strength': play['result']['strength']['code'],
                        'gameWinningGoal': play['result']['gameWinningGoal'],
                        'emptyNet': emptyNet
                    })
                # Set the shotType to None, to prevent it from being added
                shotType = { 'shotType': None }
        else:
            goal = None

        # If the eventType is 'PENALTY'; set goal dict, else empty
        if play['result']['eventTypeId'] == 'PENALTY':
            penalty = {
                'penalty': {
                    'penaltyType': play['result']['secondaryType'],
                    'penaltySeverity': play['result']['penaltySeverity'],
                    'penaltyMinutes': play['result']['penaltyMinutes']
                }
            }
            # Set the shotType to None, to prevent it from being added
            shotType = { 'shotType': None }
        else:
            penalty = None

        # Create the playDict dictionary
        playDict = {
            'eventId': play['about']['eventIdx'],
            'eventType': play['result']['eventTypeId'],
            'about': {
                'period': play['about']['period'], 
                'periodType': play['about']['periodType'],
                'periodTime': play['about']['periodTime'],
                'periodTimeRemaining': play['about']['periodTimeRemaining'],
             },
            'players': getPlayersFromPlay(play) 
        }

        # If goal is not empty, add it to playDict
        if goal is not None:
            playDict.update(goal)
        # If shotType is not empty, add it to playDict
        if shotType['shotType'] is not None:
            playDict.update(shotType)
        # If penalty is not empty, add it to playDict
        if penalty is not None:
            playDict.update(penalty)

        # Add the rest to the playDict
        playDict.update({
            'coordinates': play['coordinates'],
            'score': play['about']['goals'],
            'teams': getTeamsFromPlay(gameDict, play)
        })
        
        # Add the play to the playsArray
        playsArray.append(playDict)

    # Return the plays in form of dictionary
    return {'plays': playsArray}

''' Get teams based on the play'''
def getTeamsFromPlay(gameDict, play):
    # Simplify gameDict to info based on teams
    gameTeams = gameDict['liveData']['boxscore']['teams']

    # If the team specified in the play is the same as the home team
    if play['team']['id'] == gameTeams['home']['team']['id']:
        # The play is for the home team
        homeForAgainst = True
    else: 
        # The play is against the home team
        homeForAgainst = False

    # Create the teams dict 
    teams = {
        'away': {
            'id': gameTeams['away']['team']['id'],
            'name': gameTeams['away']['team']['name'],
            'forAgainst': not homeForAgainst
        },
        'home': {
            'id': gameTeams['home']['team']['id'],
            'name': gameTeams['home']['team']['name'],
            'forAgainst': homeForAgainst
        }
    }

    # Return teams dict
    return teams    

''' Get plays based on the play '''
def getPlayersFromPlay(play):
    # Initialize player dict
    players = {}

    # Iterate through the players
    for player in play['players']:
        # If the playerType is not specified, use 'Player'
        if player['playerType'] != 'PlayerID':
            playerType = player['playerType']
        else: 
            playerType = 'Player'

        # If the playerType = 'Assist'
        if playerType == 'Assist':
            # If the 'primaryAssist' key does not exists, set playerType to 'PrimaryAssist'
            if not 'PrimaryAssist' in player:
                playerType = 'PrimaryAssist'
            # Else set playerType to 'SecondaryAssist'
            else:
                playerType = 'SecondaryAssist'

        # Set the add to the player dict
        players[playerType] = {
            'id': player['player']['id'],
            'name': player['player']['fullName'],
            'playerType': playerType
        }

    # Return players dict
    return players

''' Get the team info based on the player id '''
def getTeamFromPlayerId(gameDict, playerId):
    # Simplify gameDict to info based on the teams 
    gameTeams = gameDict['liveData']['boxscore']['teams']

    # Get the ids for all the players on the away team
    awayPlayers = gameTeams['away']['skaters'] +  gameTeams['away']['goalies'] + gameTeams['away']['scratches']

    # If the playerId is in the list of players on the away team
    if playerId in awayPlayers:
        # Set team to away team
        team = {
            'id': gameTeams['away']['team']['id'], 
            'name': gameTeams['away']['team']['name']
        }
    else: 
        # Set team to home team
        team = {
            'id': gameTeams['home']['team']['id'], 
            'name': gameTeams['home']['team']['name']
        }
    
    # Return the team dict
    return team
