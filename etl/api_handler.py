import requests
import time
import datetime
import json
import base64
import os

api_url = 'https://apirest.wyscout.com/v3/'
current_folder = os.path.dirname(__file__)

# Preparing authentication
authentication = json.load(open(f'{current_folder}/authentication.json'))
encoded_authentication = base64.b64encode(f'{authentication["username"]}:{authentication["password"]}'.encode('ascii'))
encoded_authentication = f'Basic {encoded_authentication.decode("ascii")}'

def get_request_api(url,headers=None,params=None,retry:bool=True,sleep_time:int=0.3,retries:int=30):
    '''Requests data from API'''
    ok_response = False
    tries = 0
    while not ok_response and tries < retries:
        response = requests.get(url, headers=headers,params=params)
        if response.status_code == 200:
            ok_response = True
        # if too many requests, wait and retry
        elif response.status_code == 429 and retry:
            time.sleep(sleep_time)
        else:
            break
        tries += 1
    if not ok_response:
        print(f'Error requesting {url}, status code: {response.status_code}, message: {response.text}')
    return response.json() if ok_response else None



def get_most_updated_season(career):
    '''Gets most updated season from player career'''
    most_updated_season = None
    # get most updated season
    for entry in career:
        if not most_updated_season:
            most_updated_season = entry['season']
        else:
            if entry['season']['active']:
                most_updated_season = entry['season']
            else:
                entry_date = datetime.datetime.strptime(entry['season']['startDate'], '%Y-%m-%d')
                most_updated_season_date = datetime.datetime.strptime(most_updated_season['startDate'], '%Y-%m-%d')
                if entry_date > most_updated_season_date:
                    most_updated_season = entry['season']
        if most_updated_season['active']:
            break
    return most_updated_season


def get_latest_career_entries(career:list[dict],entries:int=5):
    '''Gets latest career entries'''
    entry_list = []
    if career:
        entry_list = sorted(career, key=lambda k: k['season']['startDate'],reverse=True)
        entry_list = entry_list[0:entries]
    return entry_list

def get_areas(retry:bool=True):
    '''Requests areas from API'''
    url = api_url + 'areas'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    areas = result['areas'] if result else []
    return areas


def get_area_competitions(area=None, retry:bool=True):
    '''Requests area's competitions from API'''
    area_competitions = []
    if area:
        url = api_url + 'competitions'
        headers = {'Authorization': encoded_authentication}
        params = {'areaId':area}
        result = get_request_api(url,headers=headers,params=params,retry=retry)
        area_competitions = result['competitions'] if result else []
    return area_competitions


def get_competition_info(competition, retry:bool=True):
    '''Requests competition info from API'''
    url = f'{api_url}competitions/{competition}'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    competition_info = result if result else None
    return competition_info

def get_seasons_competitions(competition,retry:bool=True):
    '''Requests seasons list of a competition from API'''
    url = f'{api_url}competitions/{competition}/seasons'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    seasons_list = {season['seasonId']:season['season'] for season in result['seasons']} if 'seasons' in result else {}
    return seasons_list

def get_team_info(team,retry:bool=True):
    '''Requests team info from API'''
    url = f'{api_url}teams/{team}'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    team_info = result if result else None
    return team_info



def get_match_info(match,retry:bool=True):
    '''Requests match info from API'''
    url = f'{api_url}matches/{match}'
    headers = {'Authorization': encoded_authentication}
    params = {'useSides':'true'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    match_info = result if result else None
    return match_info 


def get_player_career(player,retry:bool=True):
    '''Requests player career from API'''
    url = f'{api_url}players/{player}/career'
    headers = {'Authorization': encoded_authentication}
    params = {'details':'season'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    player_career = result['career'] if result else []
    return player_career


def get_player_advanced_stats(player,competition,season=None,retry:bool=True):
    '''Requests player advanced stats from API'''
    url = f'{api_url}players/{player}/advancedstats'
    headers = {'Authorization': encoded_authentication}
    params = {'compId':competition}
    if season:
        params['seasonId'] = season
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    player_advanced_stats = result if result else None
    return player_advanced_stats




def get_season_info(season,retry:bool=True):
    '''Requests season info from API'''
    url = f'{api_url}seasons/{season}'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    season_info = result if result else None
    return season_info

def get_season_teams(season,retry:bool=True):
    '''Requests teams from API'''
    url = f'{api_url}seasons/{season}/teams'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    teams = result['teams'] if result else []
    return teams

def get_season_standings(season,retry:bool=True):
    '''Requests season's standings from API'''
    url = f'{api_url}seasons/{season}/standings'
    headers = {'Authorization': encoded_authentication}
    params = {'details':'teams'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    standings = result['teams'] if result else []
    return standings

def get_season_career(season,retry:bool=True):
    '''Requests general performance information about all the teams for the given season from API'''
    url = f'{api_url}seasons/{season}/career'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    season_career = result['rounds'] if result else []
    return season_career


def get_season_players(season,retry:bool=True):
    '''Requests players from API\n
    Paged response, so multiple requests are made to get all players'''
    players = []
    url = f'{api_url}seasons/{season}/players'
    headers = {'Authorization': encoded_authentication}
    params = {'page':1,'limit':100}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    if result:
        meta = result['meta']
        players = result['players']
        # get all players (paged response)
        while len(players) < meta['total_items']:
            params['page'] += 1
            result = get_request_api(url,headers=headers,params=params,retry=retry)
            players += result['players']
    return players

def get_player_contract_info(player, retry:bool=True):
    '''Requests player contract info from API'''
    url = f'{api_url}players/{player}/contractinfo'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    contractInfo = result if result else None
    return contractInfo


def get_season_matches(season,retry:bool=True):
    '''Requests matches from API'''
    url = f'{api_url}seasons/{season}/matches'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    matches = result['matches'] if result else []
    return matches

def get_match_players_stats(match,retry:bool=True):
    '''Requests list of all players stats in a match from API'''
    url = f'{api_url}matches/{match}/advancedstats/players'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    players_stats = result['players'] if result else []
    return players_stats


def get_match_events(match,retry:bool=True):
    '''Requests list of all events in a match from API'''
    url = f'{api_url}matches/{match}/events'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    events = result['events'] if result else []
    return events


def get_match_lineups(match,retry:bool=True):
    '''Requests list of all lineups in a match from API'''
    url = f'{api_url}matches/{match}/formations'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    lineups = result if result else None
    return lineups