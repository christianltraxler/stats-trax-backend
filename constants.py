import datetime

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

def getScheduleUrl(year):
    startDate = str(year) + '-09-01'
    endDate = str(year + 1) + '-09-01'
    if year == 2019:
        endDate = str(year + 1) + '-10-01'
    return('https://statsapi.web.nhl.com/api/v1/schedule?startDate=' + startDate +'&endDate=' + endDate)

def getGameUrl(gameId):
    return('https://statsapi.web.nhl.com/api/v1/game/' + str(gameId) + '/feed/live')

blackListEvents = ['GAME_SCHEDULED', 'PERIOD_READY', 'PERIOD_START', 'STOP', 'PERIOD_END', 'PERIOD_OFFICIAL', 'GAME_END', 'GAME_OFFICIAL', 'SHOOTOUT_COMPLETE', 'EARLY_INT_START', 'EARLY_INT_END', 'CHALLENGE', 'EMERGENCY_GOALTENDER']
        