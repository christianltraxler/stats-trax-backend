def getAllTeamsInfoUrl():
    return ('https://statsapi.web.nhl.com/api/v1/teams/')

def getTeamInfoUrl(teamId):
    return ('https://statsapi.web.nhl.com/api/v1/teams/' + str(teamId))

def getTeamLogoUrl(abbreviation):
    return ('https://assets.nhle.com/logos/nhl/svg/' + abbreviation + '_light.svg')

def getTeamRosterUrl(teamId):
    return ('https://statsapi.web.nhl.com/api/v1/teams/' + str(teamId) + '?expand=team.roster')

def getPlayerPictureUrl(playerId, teamAbbreviation, season=2019):
    return ('https://assets.nhle.com/mugs/nhl/' + str(season) + str(season + 1) + '/' + teamAbbreviation + '/' + str(playerId) + '.png')

def getPlayerInfoUrl(playerId):
    return ('https://statsapi.web.nhl.com/api/v1/people/' + str(playerId))