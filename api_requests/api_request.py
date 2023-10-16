import datetime
import requests
import json
import os
import sys
import base64
import argparse
import time
import logging
from db import Db_handler
from multiprocessing.pool import ThreadPool
from utils import get_similar

current_folder = os.path.dirname(__file__)

api_url = 'https://apirest.wyscout.com/v3/'

# Preparing authentication
authentication = json.load(open(f'{current_folder}/authentication.json'))
encoded_authentication = base64.b64encode(f'{authentication["username"]}:{authentication["password"]}'.encode('ascii'))
encoded_authentication = f'Basic {encoded_authentication.decode("ascii")}'


def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--db_config','-dbc'            ,type=str, nargs=1,required=True                                , help='Db config json file path')
    parser.add_argument('--areas','-a'                  ,action='store_true'                                            , help='Request areas from API')
    parser.add_argument('--area_competitions','-ac'     ,type=str, nargs='+'                                            , help="Request area's competitions from API")
    parser.add_argument('--competition_info','-ci'      ,type=str, nargs='*'                                            , help="Request all info from competition from API")
    parser.add_argument('--competition_players','-cp'   ,type=str, nargs='+'                                            , help="Request competition's players from API")
    parser.add_argument('--full_info','-fi'             ,type=str, nargs=1                                              , help="Request all info from API, according to json file provided")
    parser.add_argument('--log','-l'                    ,action='store_true'                                            , help="Activate logging, with optional log file path")
    return parser.parse_args()



def run_threaded_for(func,iterable, args=None,log=False,threads:int=6):
    '''Runs a function for each value in iterable'''
    if log:
        start_time = time.time()
        print(f'Threaded: Running {func.__name__} to gather info from {len(iterable)} items ')
    iterable_divided = [None]*threads
    max_slice_size = len(iterable)//threads
    # divide work between threads
    for i in range(threads):
        if i == threads-1:
            iterable_divided[i] = iterable[i*max_slice_size:]
        else:
            iterable_divided[i] = iterable[i*max_slice_size:(i+1)*max_slice_size]
            
    thread_args = [[x,args] if args else [x] for x in iterable_divided]
    pool = ThreadPool(threads)
    results = pool.starmap(func,thread_args)
    pool.close()
    pool.join()
    if log:
        print(f'Threaded: Finished {func.__name__} in {time.time()-start_time} seconds')
    return results

        
def get_request_api(url,headers=None,params=None,retry:bool=True):
    '''Requests data from API'''
    ok_response = False
    while not ok_response:
        response = requests.get(url, headers=headers,params=params)
        if response.status_code == 200:
            ok_response = True
        if not retry:
            break
    return response.json() if ok_response else None

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

def get_player_carrer(player,retry:bool=True):
    '''Requests player carrer from API'''
    url = f'{api_url}players/{player}/career'
    headers = {'Authorization': encoded_authentication}
    params = {'details':'season'}
    result = get_request_api(url,headers=headers,params=params,retry=retry)
    player_carrer = result['career'] if result else []
    return player_carrer

def get_most_updated_season(carrer):
    '''Gets most updated season from player carrer'''
    most_updated_season = None
    # get most updated season
    for entry in carrer:
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

def get_player_advanced_stats(player,competition,retry:bool=True):
    '''Requests player advanced stats from API'''
    url = f'{api_url}players/{player}/advancedstats'
    headers = {'Authorization': encoded_authentication}
    params = {'compId':competition}
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


def get_season_players(season,retry:bool=True):
    '''Requests players from API\n
    Paged response, so multiple requests are made to get all players'''
    players = []
    url = f'{api_url}seasons/{season}/players'
    headers = {'Authorization': encoded_authentication}
    result = get_request_api(url,headers=headers,retry=retry)
    if result:
        params = {'page':1,'limit':100}
        meta = result['meta']
        players = result['players']
        # get all players (paged response)
        while len(players) < meta['total_items']:
            params['page'] += 1
            result = get_request_api(url,headers=headers,params=params,retry=retry)
            players += result['players']
    return players


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


def extract_competitions_info(competitions:list):
    '''Extracts competitions metadata (id, seasons)'''
    competitions_info = []
    # get competitions metadata (id, seasons)
    area_competitions = []
    competitions_names = []
    last_area_code = None
    for competition in competitions:
        c_i = {
            'wyId':None,
            'seasons':[]
        }
        if 'wyId' in competition:
            c_i['wyId'] = competition['wyId']
        else:
            #print('WORK IN PROGRESS. GET COMPETITION ID FROM NAME AND AREA CODE')
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
        for season in competition['seasons']:
            if 'wyId' in season:
                c_i['seasons'].append(season['wyId'])
            elif 'start' in season and 'end' in season:
                start = season['start']
                end = season['end']
                seasons_list = get_seasons_competitions(c_i['wyId'])
                seasonsId = [k for k,v in seasons_list.items() if v['startDate'][0:4] == start and v['endDate'][0:4] == end] #Neste momento so estamos a comparar os anos, se calhar deviamos ver isto melhor
                for seasonId in seasonsId:
                    c_i['seasons'].append(seasonId)
            else:
                #Error
                continue
        competitions_info.append(c_i)
    return competitions_info

def prepare_areas_insert(areas):
    '''Inserts area into db'''
    querys = []
    for area in areas:
        values = f'''({area['id']}, "{area['name']}", "{area['alpha3code']}")'''
        on_update = f'''name="{area['name']}", alpha3code="{area['alpha3code']}"'''
        querys.append(('area',values,on_update))
    return querys

def populate_areas(db_handler:Db_handler):
    '''Populates areas table in db'''
    areas = get_areas()
    result = run_threaded_for(prepare_areas_insert,areas,log=True)
    querys_list = [query for query_list in result for query in query_list]
    for query in querys_list:
        db_handler.insert_or_update(*query)




def populate_competitions(db_handler:Db_handler,competitions_id:list):
    '''Populates competitions table in db'''
    c_i = 0
    for competition_id in competitions_id:
        print(f'Requesting competition {c_i}/{len(competitions_id)}')
        competition_info = get_competition_info(competition_id)
        if competition_info:
            values = f'''({competition_info['wyId']}, "{competition_info['name']}", "{competition_info['area']['id']}", "{competition_info['gender']}"\
                , "{competition_info['type']}", "{competition_info['format']}", "{competition_info['divisionLevel']}", "{competition_info['category']}")'''
            
            on_update = f'''name="{competition_info['name']}", area="{competition_info['area']['id']}", gender="{competition_info['gender']}",\
                type="{competition_info['type']}", format="{competition_info['format']}", divisionLevel="{competition_info['divisionLevel']}", category="{competition_info['category']}"'''

            db_handler.insert_or_update('competition',values,on_update)
        c_i += 1


def populate_competitions_seasons(db_handler:Db_handler,seasons_id:list):
    '''Populates seasons table in db'''
    s_i = 0
    for season_id in seasons_id:
        print(f'Requesting season {s_i}/{len(seasons_id)}')
        season_info = get_season_info(season_id)
        if season_info:
            values = f'''({season_info['wyId']}, "{season_info['startDate']}", "{season_info['endDate']}", "{season_info['name']}", "{season_info['competitionId']}")'''
            on_update = f'''startDate="{season_info['startDate']}", endDate="{season_info['endDate']}", name="{season_info['name']}", competition="{season_info['competitionId']}"'''
            parameters = f'''(idcompetition_season, startDate, endDate, name, competition)'''
            db_handler.insert_or_update('competition_season',values,on_update,parameters)
        s_i += 1


def insert_team(teams,season_id:int):
    '''Inserts team into db, as well as team_competition_season table'''

    querys = []
    for team in teams:
        team_info = get_team_info(team['wyId'])
        if team_info:
            values = f'''({team_info['wyId']}, "{team_info['name']}", "{team_info['officialName']}", "{team_info['imageDataURL']}", "{team_info['gender']}", "{team_info['type']}",\
                "{team_info['city']}", "{team_info['category']}", "{team_info['area']['id']}")'''
            
            on_update = f'''name="{team_info['name']}", official_name="{team_info['officialName']}", icon="{team_info['imageDataURL']}", gender="{team_info['gender']}", type="{team_info['type']}",\
                city="{team_info['city']}", category="{team_info['category']}", area="{team_info['area']['id']}"'''
            
            querys.append(('team',values,on_update))

            values = f'''("{season_id}", "{team_info['wyId']}")'''
            on_update = f'''competition_season="{season_id}", team="{team_info['wyId']}"'''
            parameters = f'''(competition_season, team)'''
            querys.append(('team_competition_season',values,on_update,parameters))
    return querys

    

def populate_teams(db_handler:Db_handler,season_id:int):
    '''Populates teams table in db, as well as team_competition_season table'''
    season_info = get_season_info(season_id)
    if season_info:
        teams = get_season_teams(season_id)
        result = run_threaded_for(insert_team,teams,log=True,args=(season_id))
        querys_list = [query for query_list in result for query in query_list]
        for query in querys_list:
            db_handler.insert_or_update(*query)
        

def prepare_players_insert(players,player_advanced_stats:bool=False):
    querys = []
    for player in players:
        player_name = player['firstName'] + ' ' + player['middleName'] + ' ' + player['lastName']
        values = f'''({player['wyId']}, "{player_name}", "{player['shortName']}", "{player['birthArea']['id']}", "{player['birthDate']}", "{player['imageDataURL']}", "{player['foot']}",\
        "{player['height']}","{player['weight']}","{player['status']}","{player['gender']}","{player['role']['code2']}", "{player['role']['code3']}", "{player['role']['name']}")'''

        on_update = f'''name="{player_name}", short_name="{player['shortName']}", birth_area="{player['birthArea']['id']}", birth_date="{player['birthDate']}", image="{player['imageDataURL']}", foot="{player['foot']}",\
        height="{player['height']}", weight="{player['weight']}", status="{player['status']}", gender="{player['gender']}", role_code2="{player['role']['code2']}", role_code3="{player['role']['code3']}", role_name="{player['role']['name']}"'''
        
        querys.append(('player',values,on_update))

        # get player advanced stats
        if player_advanced_stats:
            carrer = get_player_carrer(player['wyId'])
            most_updated_season = get_most_updated_season(carrer)
            if most_updated_season:
                advanced_stats = get_player_advanced_stats(player['wyId'],most_updated_season['competitionId'])
                if advanced_stats:
                    # populate positions table
                    positions = advanced_stats['positions']
                    for position in positions:
                        values = f'''("{player['wyId']}", "{position['percent']}","{position['position']['code']}", "{position['position']['name']}")'''
                        on_update = f'''player="{player['wyId']}", percent="{position['percent']}", code="{position['position']['code']}", name="{position['position']['name']}"'''
                        parameters = f'''(player, percent, code, name)'''
                        querys.append(('player_positions',values,on_update,parameters))
    return querys
        
    

def populate_players(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates players table in db'''
    players = get_season_players(season_id)
    result = run_threaded_for(prepare_players_insert,players,log=True,args=(player_advanced_stats),threads=10)
    querys_list = [query for query_list in result for query in query_list]
    for query in querys_list:
        db_handler.insert_or_update(*query)


def prepare_matches_insert(matches,player_advanced_stats:bool=False):
    querys = []
    for match in matches:
        match_info = get_match_info(match['matchId'])
        if match_info:
            home_team = match_info['teamsData']['home']['teamId']
            home_score = match_info['teamsData']['home']['score']
            away_team = match_info['teamsData']['away']['teamId']
            away_score = match_info['teamsData']['away']['score']
            winner = match_info['winner']
            values = f'''({match_info['wyId']}, "{match_info['seasonId']}", "{home_team}", "{away_team}", "{match_info['dateutc']}",\
            "{home_score}","{away_score}", "{winner}")'''

            on_update = f'''competition_season="{match_info['seasonId']}", home_team="{home_team}", away_team="{away_team}", date="{match_info['dateutc']}",\
            home_score="{home_score}", away_score="{away_score}", winner="{winner}"'''

            querys.append(('match',values,on_update))
            # get match advanced stats for each player
            if player_advanced_stats:
                query_list = prepare_match_players_stats_insert(match['matchId'])
                querys += query_list
    return querys
        


def populate_matches(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates matches table in db, gathering matches from given season\n
    Can gather advanced stats from players in each match'''
    matches = get_season_matches(season_id)
    result = run_threaded_for(prepare_matches_insert,matches,log=True,args=(player_advanced_stats))
    querys_list = [query for query_list in result for query in query_list]
    for query in querys_list:
        db_handler.insert_or_update(*query)
    

def prepare_match_players_stats_insert(match:int):
    '''Populates player_match_stats table in db'''
    querys = []
    match_players_stats = get_match_players_stats(match)
    for player_stats in match_players_stats:
        player = player_stats['playerId']
        offensive_duels = player_stats['total']['offensiveDuels']
        progressive_passes = player_stats['total']['progressivePasses']
        forward_passes = player_stats['total']['forwardPasses']
        crosses = player_stats['total']['crosses']
        key_passes = player_stats['total']['keyPasses']
        defensive_duels = player_stats['total']['defensiveDuels']
        interceptions = player_stats['total']['interceptions']
        recoveries = player_stats['total']['recoveries']
        successful_passes = player_stats['percent']['successfulPasses']
        long_passes = player_stats['total']['longPasses']
        aerial_duels = player_stats['total']['aerialDuels']
        losses = player_stats['total']['losses']
        own_half_losses = player_stats['total']['ownHalfLosses']
        goal_kicks = player_stats['total']['goalKicks']
        received_pass = player_stats['total']['receivedPass']
        dribbles = player_stats['total']['dribbles']
        touch_in_box = player_stats['total']['touchInBox']

        values = f'''("{match}", "{player}", "{offensive_duels}", "{progressive_passes}", "{forward_passes}", "{crosses}", "{key_passes}", "{defensive_duels}", "{interceptions}", "{recoveries}",\
        "{successful_passes}", "{long_passes}", "{aerial_duels}", "{losses}", "{own_half_losses}", "{goal_kicks}", "{received_pass}", "{dribbles}", "{touch_in_box}")'''

        on_update = f'''`match`="{match}", player="{player}", offensiveDuels="{offensive_duels}", progressivePasses="{progressive_passes}", forwardPasses="{forward_passes}", crosses="{crosses}", keyPasses="{key_passes}", defensiveDuels="{defensive_duels}", interceptions="{interceptions}", recoveries="{recoveries}",\
        successfulPasses="{successful_passes}", longPasses="{long_passes}", aerialDuels="{aerial_duels}", losses="{losses}", ownHalfLosses="{own_half_losses}", goalKicks="{goal_kicks}", receivedPass="{received_pass}", dribbles="{dribbles}", touchInBox="{touch_in_box}"'''

        parameters = f'''(`match`, player, offensiveDuels, progressivePasses, forwardPasses, crosses, keyPasses, defensiveDuels, interceptions, recoveries,\
        successfulPasses, longPasses, aerialDuels, losses, ownHalfLosses, goalKicks, receivedPass, dribbles, touchInBox)'''

        querys.append(('player_match_stats',values,on_update,parameters))
    return querys


def main(args,db_handler:Db_handler):
    '''Main function'''

    #TODO : treat other optional flags

    # get full info
    if args.full_info:
        request_file_path = f'{current_folder}/{args.full_info[0]}'
        if request_file_path.endswith('json') and os.path.exists(request_file_path):
            request_file = json.load(open(request_file_path))
            # populate areas
            populate_areas(db_handler) 
            if 'competitions' in request_file:
                competitions = request_file['competitions']
                competitions_info = extract_competitions_info(competitions)
                #print(competitions_info)
                competitions_id = [c['wyId'] for c in competitions_info]
                # populate competitions
                populate_competitions(db_handler,competitions_id)

                # populate seasons
                seasons_id = [s for c in competitions_info for s in c['seasons']]
                populate_competitions_seasons(db_handler,seasons_id)

                s_i = 0
                # populate teams, players, matches and stats
                for s_id in seasons_id:
                    print(f'Extracting info from season {s_i}/{len(seasons_id)}')
                    populate_teams(db_handler,s_id)
                    populate_players(db_handler,s_id,player_advanced_stats=True)
                    populate_matches(db_handler,s_id,player_advanced_stats=True)
                    s_i += 1

        else:
            print('Invalid request file. Please provide a valid .json file.')




if __name__ == '__main__':
    args = parse_arguments()

    if args.db_config[0].endswith('.json'):
        db_config_path = f'{current_folder}/{args.db_config[0]}'
        db_logger = None
        main_logger = None
        if args.log:
            logging.basicConfig(level=logging.INFO)
            db_logger = logging.getLogger('db_logger')
            main_logger = logging.getLogger('main_logger')
            main_logger.log(logging.INFO,'Logging active')
        db_handler = Db_handler(config_json=db_config_path,logger=db_logger)
        db_handler.create_connection()
        if db_handler.connection:
            main(args,db_handler)
            db_handler.close_connection()
        else:
            print('DB connection failed to be established.')
    else:
        print('Invalid db config file. Please provide a .json file.')



                        