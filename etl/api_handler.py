import requests
import time
import datetime
import json
import base64
import os
from utils import get_similar

api_url = 'https://apirest.wyscout.com/v3/'
current_folder = os.path.dirname(__file__)

# Preparing authentication
authentication = json.load(open(f'{current_folder}/api_cred.json'))
encoded_authentication = base64.b64encode(f'{authentication["username"]}:{authentication["password"]}'.encode('ascii'))
encoded_authentication = f'Basic {encoded_authentication.decode("ascii")}'

def get_request_api(url,headers=None,params=None,retry:bool=True,sleep_time:int=0.3,retries:int=30):
    '''Requests data from API'''
    ok_response = False
    tries = 0
    while not ok_response and tries < retries:
        try:
            response = requests.get(url, headers=headers,params=params,timeout=30)
            if response.status_code == 200:
                ok_response = True
            # if too many requests, wait and retry
            elif response.status_code == 429 and retry:
                time.sleep(sleep_time)
            else:
                break
            tries += 1
        except Exception as e:
            print(f'Error requesting {url}, message: {e}')
            tries += 1
            if retry and tries < retries:
                time.sleep(sleep_time)
            else:
                break
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


def get_season_career_entries(career:list[dict],season_id:int):
    '''Gets latest career entries'''
    entry_list = []
    if career:
        entry_list = [k for k in career if k['seasonId'] == season_id]
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

def get_season_info(season, retry:bool=True):
    '''Request season info from API'''
    url = f'{api_url}seasons/{season}'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    season_info = result if result else None
    return season_info

def get_seasons_info_competitions(competition,retry:bool=True):
    '''Requests seasons list of a competition from API'''
    url = f'{api_url}competitions/{competition}/seasons'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    seasons_list = result if result else None
    return seasons_list

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
    params = {'useSides':'true','details':'players'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    match_info = result if result else None
    return match_info 

def get_match_advanced_stats(match,retry:bool=True):
    '''Requests match advanced stats from API'''
    url = f'{api_url}matches/{match}/advancedstats'
    headers = {'Authorization': encoded_authentication}
    params = {'useSides':'true','details':'match,teams'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    match_advanced_stats = result if result else None
    return match_advanced_stats


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


def get_player_last_transfer(player,retry:bool=True):
    '''Requests player last transfer from API'''
    url = f'{api_url}players/{player}/transfers'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    last_transfer = None
    if result:
        transfers_list = result['transfer'] if 'transfer' in result else []
        latest_time = None
        # get latest transfer
        for transfer in transfers_list:
            try:
                if transfer['startDate']:
                    transfer_time = datetime.datetime.strptime(transfer['startDate'], '%Y-%m-%d')
                    if not last_transfer:
                        last_transfer = transfer
                        latest_time = transfer_time
                    else:
                        if transfer_time > latest_time:
                            last_transfer = transfer
                            latest_time = transfer_time
            except:
                pass
    return last_transfer




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
    if standings:
        unique_teams = {}
        for team in standings:
            if team['teamId'] not in unique_teams:
                unique_teams[team['teamId']] = team
            else:
                if team['totalPlayed'] > unique_teams[team['teamId']]['totalPlayed']:
                    unique_teams[team['teamId']] = team
        standings = list(unique_teams.values())
    return standings

def get_season_career(season,retry:bool=True):
    '''Requests general performance information about all the teams for the given season from API'''
    url = f'{api_url}seasons/{season}/career'
    headers = {'Authorization': encoded_authentication}
    params = {'details':'round,team'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
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

def get_update_matches(date,retry:bool=True):
    '''Requests matches updateobjects from API'''
    url = f'{api_url}/updatedobjects'
    headers = {'Authorization': encoded_authentication}
    params = {'updated_since':date,
              'emptyPayload' : True,
              'type' : 'matches'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    matches = result['matches'] if result else []
    return matches

def get_match_players_stats(match,players:bool=False,retry:bool=True):
    '''Requests list of all players stats in a match from API'''
    url = f'{api_url}matches/{match}/advancedstats/players'
    headers = {'Authorization': encoded_authentication}
    params = None
    if players:
        params = {'details':'player'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
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

def extract_competitions_info(competitions:list):
    '''Extracts competitions metadata (id, seasons) from json config file'''
    competitions_info = {}
    competition_list = []
    area_competitions = []
    competitions_names = []
    last_area_code = None
    for competition in competitions:
        c_i = {
            'wyId':None,
            "name": None,
            "area": None,
            'custom_name' : None,
            'tm_code':None,
            'seasons':[]
        }
        if 'wyId' in competition:
            c_i['wyId'] = competition['wyId']
        else:
            if 'area' in competition and 'name' in competition:
                areaCode = competition['area']
                competition_name = competition['name']
                if areaCode != last_area_code: #Como ele recebe uma lista de competiçoes no ficheiro, se estas forem todas da mesma área é escusado estar sempre a ir buscar a informaçao a api para encontrar o id delas
                    area_competitions = get_area_competitions(area=areaCode)
                    competitions_names = [c['name'] for c in area_competitions]
                else:
                    last_area_code = areaCode
                true_competition_name = get_similar(competitions_names,competition_name)
                c_i['wyId'] = [c['wyId'] for c in area_competitions if c['name'] == true_competition_name][0]
            else:
                #ERROR
                continue
        if 'tm_code' in competition:
            c_i['custom_name'] = competition['tm_code']
            c_i['tm_code'] = competition['tm_code']
        if 'name' in competition:
            c_i['name'] = competition['name']
        if 'area' in competition:
            c_i['area'] = competition['area']
        for season in competition['seasons']:
            if 'wyId' in season and season['wyId'] not in c_i['seasons']:
                c_i['seasons'].append(season['wyId'])
            elif 'start' in season and 'end' in season:
                start = season['start']
                end = season['end']
                seasons_list = get_seasons_competitions(c_i['wyId'])
                seasonsId = [k for k,v in seasons_list.items() if v['startDate'][0:4] == start and v['endDate'][0:4] == end] #Neste momento so estamos a comparar os anos, se calhar deviamos ver isto melhor
                for seasonId in seasonsId:
                    if seasonId not in c_i['seasons']:
                        c_i['seasons'].append(seasonId)
            else:
                #Error
                continue
        competitions_info[c_i['wyId']]=c_i
        if c_i['wyId'] not in competition_list:
            competition_list.append(c_i['wyId'])

    return [competitions_info[c] for c in competition_list]


def get_season_scorers(season:int,retry:bool=True):
    '''Requests season's scorers from API'''
    url = f'{api_url}seasons/{season}/scorers'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    scorers = result['players'] if result else []
    return scorers


def get_season_assistmen(season:int,retry:bool=True):
    '''Requests season's assistmen from API'''
    url = f'{api_url}seasons/{season}/assistmen'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    assistmen = result['players'] if result else []
    return assistmen