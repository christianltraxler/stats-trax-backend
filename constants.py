def getAllTeamsInfoUrl():
    return ("https://statsapi.web.nhl.com/api/v1/teams/")

def getTeamInfoUrl(teamId):
    return ("https://statsapi.web.nhl.com/api/v1/teams/" + str(teamId))