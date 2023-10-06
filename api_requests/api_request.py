import requests
import json
import os
import base64
import argparse

current_folder = os.path.dirname(__file__)

api_url = 'https://apirest.wyscout.com/v3/'

# Preparing authentication
authentication = json.load(open('authentication.json'))
encoded_authentication = base64.b64encode(f'{authentication["username"]}:{authentication["password"]}'.encode('ascii'))
encoded_authentication = f'Basic {encoded_authentication.decode("ascii")}'


def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--areas','-a',action='store_true', help='Request areas from API')
    parser.add_argument('--area_competitions','-ac',type=str, nargs='+' , help="Request area's competitions from API")
    return parser.parse_args()



def get_areas():
    '''Requests areas from API'''
    url = api_url + 'areas'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    return response.json()


def get_area_competitions(areas=None):
    '''Requests competitions from API'''
    result = []
    if areas:
        url = api_url + 'competitions'
        headers = {'Authorization': encoded_authentication}
        for area in areas:
            response = requests.get(url, headers=headers,params={'areaId':area})
            result.append(response.json())
    return result



if __name__ == '__main__':
    args = parse_arguments()

    if args.areas:
        areas = get_areas()
        print(areas)
        json.dump(areas, open(f'{current_folder}/data/areas.json', 'w'), indent=4)

    if args.area_competitions:
        competitions = get_area_competitions(args.area_competitions)
        print(competitions)
        json.dump(competitions, open(f'{current_folder}/data/competitions.json', 'w'), indent=4)

    match = json.load(open(f'{current_folder}/data/matches.json'))
    print(len(match['events']))




