import requests
import json
import os
import base64
import argparse
import time
from threading import Thread
from threading import Semaphore


current_folder = os.path.dirname(__file__)

api_url = 'https://apirest.wyscout.com/v3/'

# Preparing authentication
authentication = json.load(open(f'{current_folder}/authentication.json'))
encoded_authentication = base64.b64encode(f'{authentication["username"]}:{authentication["password"]}'.encode('ascii'))
encoded_authentication = f'Basic {encoded_authentication.decode("ascii")}'


def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--areas','-a'                  ,action='store_true'                         , help='Request areas from API')
    parser.add_argument('--area_competitions','-ac'     ,type=str, nargs='+'                         , help="Request area's competitions from API")
    parser.add_argument('--competition_info','-ci'      ,type=str, nargs='*'                         , help="Request all info from competition from API")
    parser.add_argument('--competition_players','-cp'   ,type=str, nargs='+'                           , help="Request competition's players from API")
    return parser.parse_args()



def get_areas():
    '''Requests areas from API'''
    url = api_url + 'areas'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    return response.json()


def get_area_competitions(area=None):
    '''Requests area's competitions from API'''
    result = []
    if area:
        url = api_url + 'competitions'
        headers = {'Authorization': encoded_authentication}
        response = requests.get(url, headers=headers,params={'areaId':area})
        result = response.json()['competitions']
    return result


def get_competition_info(competition):
    '''Requests competition info from API'''
    url = f'{api_url}competitions/{competition}'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    return response.json()


def get_competition_teams(competition):
    '''Requests teams from API'''
    url = f'{api_url}competitions/{competition}/teams'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    return response.json()

def get_competition_players(competition):
    '''Requests players from API\n
    Paged response, so multiple requests are made to get all players'''
    players = []
    url = f'{api_url}competitions/{competition}/players'
    headers = {'Authorization': encoded_authentication}
    params = {'count':0,'limit':100}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        meta = result['meta']
        players = result['players']
        # get all players (paged response)
        while len(players) < meta['total_items']:
            params['count'] = len(players)
            response = requests.get(url, headers=headers,params=params)
            result = response.json()
            players += result['players']
    return players

def get_competition_matches(competition):
    '''Requests matches from API'''
    url = f'{api_url}competitions/{competition}/matches'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    return response.json()


def get_team_info(team):
    '''Requests team info from API'''
    url = f'{api_url}teams/{team}'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    return response.json()



def get_match_events(match):
    '''Requests match events from API'''
    url = f'{api_url}matches/{match}/events'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    return response.json()




def get_player_info(player):
    '''Requests player info from API'''
    url = f'{api_url}players/{player}'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    return response.json()



def get_and_save_match_events(match_id,file,log=None,lock=None,sleep_time=0):
    '''Requests match events from API and saves them to file'''
    if lock:
        with lock:
            print('in lock')
            match_events = get_match_events(match_id)
            time.sleep(sleep_time)
    else:
        match_events = get_match_events(match_id)
    if file:
        json.dump(match_events, open(file, 'w'), indent=4)
    if log:
        print(log)
    return match_events


def get_competition_events(matches, area, competition):
    '''Requests all competition matches events from API'''
    semaphore = Semaphore(6)
    workers = []
    j = 0
    for match in matches:
        log = f'Requested matches: {j}/{len(matches)}'
        file = f'{current_folder}/data/{area}/{competition["wyId"]}/matches/{match["matchId"]}_{match["label"]}.json'
        worker = Thread(target=get_and_save_match_events, args=(match['matchId'],file,log,semaphore,0.5),daemon=True)
        workers.append(worker)
        worker.start()
        j += 1 

    for worker in workers:
        worker.join()


def main():
    args = parse_arguments()

    # get areas
    if args.areas:
        areas = get_areas()
        print(areas)
        json.dump(areas, open(f'{current_folder}/data/areas.json', 'w'), indent=4)

    # get areas' competitions
    if args.area_competitions:
        for area in args.area_competitions:
            competitions = get_area_competitions(area)
            print(competitions)
            if competitions:
                if not os.path.isdir(f'{current_folder}/data/{area}'):
                    os.mkdir(f'{current_folder}/data/{area}')
                
                json.dump(competitions, open(f'{current_folder}/data/{area}/competitions.json', 'w'), indent=4)

    # get competitions info
    if args.competition_info:
        if competitions or args.competitions_info:
            if args.competitions_info:
                competitions = args.competitions_info
        i = 0
        for competition in competitions:
            print(f'Requested competitions: {i}/{len(competitions)}')
            competition_info = get_competition_info(competition)
            area = competition_info['area']['alpha3code']
            if not os.path.isdir(f'{current_folder}/data/{area}/{competition["wyId"]}'):
                os.mkdir(f'{current_folder}/data/{area}/{competition["wyId"]}')
            competition_players = get_competition_players(competition['wyId'])
            competition_teams = get_competition_teams(competition['wyId'])
            competition_matches = get_competition_matches(competition['wyId'])
            json.dump(competition_players, open(f'{current_folder}/data/{area}/{competition["wyId"]}/players.json', 'w'), indent=4)
            json.dump(competition_teams, open(f'{current_folder}/data/{area}/{competition["wyId"]}/teams.json', 'w'), indent=4)
            json.dump(competition_matches, open(f'{current_folder}/data/{area}/{competition["wyId"]}/matches.json', 'w'), indent=4)

            # get matches events
            if not os.path.isdir(f'{current_folder}/data/{area}/{competition["wyId"]}/matches'):
                os.mkdir(f'{current_folder}/data/{area}/{competition["wyId"]}/matches')
            competition_matches = competition_matches['matches']

            get_competition_events(competition_matches, area, competition)
            i += 1

    # get competitions players
    if args.competition_players:
        competitions = args.competition_players
        for competition in competitions:
            competition_info = get_competition_info(competition)
            area = competition_info['area']['alpha3code']
            if not os.path.isdir(f'{current_folder}/data/{area}/{competition}'):
                os.mkdir(f'{current_folder}/data/{area}/{competition}')
            competition_players = get_competition_players(competition)
            json.dump(competition_players, open(f'{current_folder}/data/{area}/{competition}/players.json', 'w'), indent=4)



if __name__ == '__main__':
    main()


                        