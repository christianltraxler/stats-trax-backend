import json
import requests

from pymongo import MongoClient

import constants

''' Adds all the active countries to the stats_trax.countries'''
def addCountries(db):
    # Get the dictionary of the info of all the countries
    countriesDict = requests.get(constants.getCountriesUrl()).json()['data']

    # Iterate through all the countries
    # For each countries, either add it to the dictionary or skip if it already exists
    for countryInfo in countriesDict:
        # Based on the info of the country, generate a dictionary 
        country = {
            'id': countryInfo['id'],
            'name': countryInfo['countryName'],
            'code': countryInfo['countryCode'],
            'nationalityName': countryInfo['nationalityName'],
            'flag' : {
                'link': countryInfo['imageUrl']
            }
        }

        # Find any existing countries in the database with the same id
        dbCountry = db.countries.find_one({'id': countryInfo['id']})
        # Removed the _id key to compare the new dictionary with the one from the collection
        if (dbCountry != None):
            dbCountry.pop('_id')

        # If the new and collection dictionaries are different
        if (dbCountry != country):
            print('Resetting team: ' + country['name'])
            # Delete the existing info from the collection
            db.countries.delete_one({'id': countryInfo['id']})
            # Add the new info into the collection
            db.countries.insert_one(country)
        else:
            print('Skipping country: ' + country['name'])
