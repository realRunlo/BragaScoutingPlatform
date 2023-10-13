import datetime
import requests
import json
import os
import sys
import base64
import argparse
import time
from threading import Thread
from threading import Semaphore
from db import Db_handler

current_folder = os.path.dirname(__file__)

api_url = 'https://apirest.wyscout.com/v3/'

# Preparing authentication
authentication = json.load(open(f'{current_folder}/authentication.json'))
encoded_authentication = base64.b64encode(f'{authentication["username"]}:{authentication["password"]}'.encode('ascii'))
encoded_authentication = f'Basic {encoded_authentication.decode("ascii")}'


def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--db_config','-dbc'            ,type=str, nargs=1,required=True             , help='Db config json file path')
    parser.add_argument('--areas','-a'                  ,action='store_true'                         , help='Request areas from API')
    parser.add_argument('--area_competitions','-ac'     ,type=str, nargs='+'                         , help="Request area's competitions from API")
    parser.add_argument('--competition_info','-ci'      ,type=str, nargs='*'                         , help="Request all info from competition from API")
    parser.add_argument('--competition_players','-cp'   ,type=str, nargs='+'                         , help="Request competition's players from API")
    parser.add_argument('--full_info','-fi'             ,type=str, nargs=1                           , help="Request all info from API, according to json file provided")
    return parser.parse_args()



def get_areas():
    '''Requests areas from API'''
    areas = []
    url = api_url + 'areas'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        areas = response.json()['areas']
    return areas


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
    competition_info = None
    url = f'{api_url}competitions/{competition}'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        competition_info = response.json()
    return competition_info

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


def get_match_info(match):
    '''Requests match info from API'''
    match_info = None
    url = f'{api_url}matches/{match}'
    headers = {'Authorization': encoded_authentication}
    params = {'useSides':'true'}
    response = requests.get(url, headers=headers,params=params)
    if response.status_code == 200:
        match_info = response.json()
    return match_info 



def get_player_info(player):
    '''Requests player info from API'''
    player_info = None
    url = f'{api_url}players/{player}'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        player_info = response.json()
    return player_info


def get_player_carrer(player):
    '''Requests player carrer from API'''
    player_carrer = None
    url = f'{api_url}players/{player}/career'
    headers = {'Authorization': encoded_authentication}
    params = {'details':'season'}
    response = requests.get(url, headers=headers,params=params)
    if response.status_code == 200:
        player_carrer = response.json()['career']
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

def get_player_advanced_stats(player,competition):
    '''Requests player advanced stats from API'''
    player_advanced_stats = None
    url = f'{api_url}players/{player}/advancedstats'
    headers = {'Authorization': encoded_authentication}
    params = {'compId':competition}
    response = requests.get(url, headers=headers,params=params)
    if response.status_code == 200:
        player_advanced_stats = response.json()
    return player_advanced_stats



def get_and_save_match_events(match_id,file,log=None,lock=None,sleep_time=0):
    '''Requests match events from API and saves them to file'''
    if lock:
        with lock:
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


def get_season_info(season):
    '''Requests season info from API'''
    season_info = None
    url = f'{api_url}seasons/{season}'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        season_info = response.json()
    return season_info

def get_season_teams(season):
    '''Requests teams from API'''
    teams = []
    url = f'{api_url}seasons/{season}/teams'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        teams = response.json()['teams']
    return teams


def get_season_players(season):
    '''Requests players from API\n
    Paged response, so multiple requests are made to get all players'''
    players = []
    url = f'{api_url}seasons/{season}/players'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
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


def get_season_matches(season):
    '''Requests matches from API'''
    matches = []
    url = f'{api_url}seasons/{season}/matches'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        matches = response.json()['matches']
    return matches

def get_match_players_stats(match):
    '''Requests list of all players stats in a match from API'''
    players_stats = []
    url = f'{api_url}matches/{match}/advancedstats/players'
    headers = {'Authorization': encoded_authentication}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        players_stats = response.json()['players']
    return players_stats


def extract_competitions_info(competitions:list):
    '''Extracts competitions metadata (id, seasons)'''
    competitions_info = []
    # get competitions metadata (id, seasons)
    for competition in competitions:
        c_i = {
            'wyId':None,
            'seasons':[]
        }
        if 'wyId' in competition:
            c_i['wyId'] = competition['wyId']
        else:
            #TODO
            print('WORK IN PROGRESS. GET COMPETITION ID FROM NAME AND AREA CODE')
            continue
        for season in competition['seasons']:
            if 'wyId' in season:
                c_i['seasons'].append(season['wyId'])
            else:
                #TODO
                print('WORK IN PROGRESS. GET SEASON ID FROM DATE')
        competitions_info.append(c_i)
    return competitions_info


def populate_areas(db_handler:Db_handler):
    '''Populates areas table in db'''
    areas = get_areas()
    for area in areas:
        values = f'''({area['id']}, "{area['name']}", "{area['alpha3code']}")'''
        on_update = f'''name="{area['name']}", alpha3code="{area['alpha3code']}"'''
        db_handler.insert_or_update('area',values,on_update)



def populate_competitions(db_handler:Db_handler,competitions_id:list):
    '''Populates competitions table in db'''
    for competition_id in competitions_id:
        competition_info = get_competition_info(competition_id)
        if competition_info:
            values = f'''({competition_info['wyId']}, "{competition_info['name']}", "{competition_info['area']['id']}", "{competition_info['gender']}"\
                , "{competition_info['type']}", "{competition_info['format']}", "{competition_info['divisionLevel']}", "{competition_info['category']}")'''
            
            on_update = f'''name="{competition_info['name']}", area="{competition_info['area']['id']}", gender="{competition_info['gender']}",\
                type="{competition_info['type']}", format="{competition_info['format']}", divisionLevel="{competition_info['divisionLevel']}", category="{competition_info['category']}"'''

            db_handler.insert_or_update('competition',values,on_update)


def populate_competitions_seasons(db_handler:Db_handler,seasons_id:list):
    '''Populates seasons table in db'''
    for season_id in seasons_id:
        season_info = get_season_info(season_id)
        if season_info:
            values = f'''({season_info['wyId']}, "{season_info['startDate']}", "{season_info['endDate']}", "{season_info['name']}", "{season_info['competitionId']}")'''
            on_update = f'''startDate="{season_info['startDate']}", endDate="{season_info['endDate']}", name="{season_info['name']}", competition="{season_info['competitionId']}"'''
            parameters = f'''(idcompetition_season, startDate, endDate, name, competition)'''
            db_handler.insert_or_update('competition_season',values,on_update,parameters)


def populate_teams(db_handler:Db_handler,season_id:int):
    '''Populates teams table in db, as well as team_competition_season table'''
    season_info = get_season_info(season_id)
    if season_info:
        teams = get_season_teams(season_id)
        for team in teams:
            team_info = get_team_info(team['wyId'])
            if team_info:
                values = f'''({team_info['wyId']}, "{team_info['name']}", "{team_info['officialName']}", "{team_info['imageDataURL']}", "{team_info['gender']}", "{team_info['type']}",\
                    "{team_info['city']}", "{team_info['category']}", "{team_info['area']['id']}")'''
                
                on_update = f'''name="{team_info['name']}", official_name="{team_info['officialName']}", icon="{team_info['imageDataURL']}", gender="{team_info['gender']}", type="{team_info['type']}",\
                    city="{team_info['city']}", category="{team_info['category']}", area="{team_info['area']['id']}"'''
                
                db_handler.insert_or_update('team',values,on_update)

                values = f'''("{season_id}", "{team_info['wyId']}")'''
                on_update = f'''competition_season="{season_id}", team="{team_info['wyId']}"'''
                parameters = f'''(competition_season, team)'''
                db_handler.insert_or_update('team_competition_season',values,on_update,parameters)


def populate_players(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates players table in db'''
    players = get_season_players(season_id)
    for player in players:
        player_name = player['firstName'] + ' ' + player['middleName'] + ' ' + player['lastName']
        values = f'''({player['wyId']}, "{player_name}", "{player['shortName']}", "{player['birthArea']['id']}", "{player['birthDate']}", "{player['imageDataURL']}", "{player['foot']}",\
        "{player['height']}","{player['weight']}","{player['status']}","{player['gender']}","{player['role']['code2']}", "{player['role']['code3']}", "{player['role']['name']}")'''

        on_update = f'''name="{player_name}", short_name="{player['shortName']}", birth_area="{player['birthArea']['id']}", birth_date="{player['birthDate']}", image="{player['imageDataURL']}", foot="{player['foot']}",\
        height="{player['height']}", weight="{player['weight']}", status="{player['status']}", gender="{player['gender']}", role_code2="{player['role']['code2']}", role_code3="{player['role']['code3']}", role_name="{player['role']['name']}"'''
        
        db_handler.insert_or_update('player',values,on_update)

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
                        on_update = f'''player="{player['wyId']}", percent="{position['percent']}", code="{position['code']}", name="{position['name']}"'''
                        parameters = f'''(player, percent, code, name)'''
                        db_handler.insert_or_update('position',values,on_update,parameters)

def populate_matches(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates matches table in db, gathering matches from given season\n
    Can gather advanced stats from players in each match'''
    matches = get_season_matches(season_id)

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

            db_handler.insert_or_update('match',values,on_update)
            # get match advanced stats for each player
            if player_advanced_stats:
                populate_match_players_stats(db_handler,match['matchId'])
        

def populate_match_players_stats(db_handler:Db_handler,match:int):
    '''Populates player_match_stats table in db'''
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

        db_handler.insert_or_update('player_match_stats',values,on_update,parameters)


def main(args,db_handler:Db_handler):
    
    # get areas
    if args.areas:
        areas = get_areas()
        json.dump(areas, open(f'{current_folder}/data/areas.json', 'w'), indent=4)

    # get areas' competitions
    if args.area_competitions:
        for area in args.area_competitions:
            competitions = get_area_competitions(area)
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
                competitions_id = [c['wyId'] for c in competitions_info]
                # populate competitions
                populate_competitions(db_handler,competitions_id)

                # populate seasons
                seasons_id = [s for c in competitions_info for s in c['seasons']]
                populate_competitions_seasons(db_handler,seasons_id)

                # populate teams, players, matches and stats
                for s_id in seasons_id:
                    populate_teams(db_handler,s_id)
                    populate_players(db_handler,s_id,player_advanced_stats=True)
                    populate_matches(db_handler,s_id,player_advanced_stats=True)


                
        else:
            print('Invalid request file. Please provide a valid .json file.')




if __name__ == '__main__':
    args = parse_arguments()

    if args.db_config[0].endswith('.json'):
        db_config_path = f'{current_folder}/{args.db_config[0]}'
        db_handler = Db_handler(config_json=db_config_path)
        db_handler.create_connection()
        if db_handler.connection:
            main(args,db_handler)
        else:
            print('DB connection failed to be established.')
    else:
        print('Invalid db config file. Please provide a .json file.')



                        