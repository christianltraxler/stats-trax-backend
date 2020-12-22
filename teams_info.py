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
            'roster': getRosters(teamInfo['id'], 2015, 2021),
            'teamStats': getTeamStats(teamInfo['id'], 2015, 2020),
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

''' Cycle through all the years specified to get the team rosters for that year '''
def getRosters(teamId, startYear, endYear):
    # Initialize rosters (to be returned) and year variable to cycle
    rosters = {}
    year = startYear

    # Cycle through all the years specified
    while (year < endYear):
        # For VGK, if the year is less than 2017, change the year to 2017 (their first season)
        if (teamId == 54 and year < 2017):
            year = 2017

        # Initialize the roster dict for the season
        rosters[str(year) + str(year + 1)] = {}

        # Get the team roster for the season
        teamRoster = requests.get(constants.getTeamRosterForSeason(year, teamId)).json()
        
        # Cycle through the players in the roster
        for player in teamRoster['roster']:
            # Create the player dict based on the player's id
            rosters[str(year) + str(year + 1)][str(player['person']['id'])] = {
                'id': player['person']['id'],
                'name': player['person']['fullName']
            }
        # Increment the year 
        year = year + 1

    # Return the rosters
    return rosters

''' Cycle through all the years specified to get the team stats for the year '''
def getTeamStats(teamId, startYear, endYear): 
    # Initialize stats (to be returned) and year variable to cycle
    stats = {}
    year = startYear

    # Cycle through all the years specified
    while (year < endYear):
        # For VGK, if the year is less than 2017, change the year to 2017 (their first season)
        if (teamId == 54 and year < 2017):
            year = 2017

        # Initialize the stats dict for the season
        stats[str(year) + str(year + 1)] = {}

        # Get the team stats for the season
        teamStats = requests.get(constants.getTeamStatsForSeason(year, teamId)).json()
        
        # Create the stats dict based on the teamStats json
        stats[str(year) + str(year + 1)] = {
            'numbers': teamStats['teams'][0]['teamStats'][0]['splits'][0]['stat'],
            'rankings': teamStats['teams'][0]['teamStats'][0]['splits'][1]['stat']
        }
        # Increment the year 
        year = year + 1

    # Return the stats dict
    return stats
