import json
import os
import argparse
import time
import logging
from db import Db_handler
from multiprocessing.pool import ThreadPool
from utils import get_similar
from api_handler import *
from tqdm import tqdm

pbar_players = tqdm()
pbar_matches = tqdm()



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



def run_threaded_for(func,iterable:list, args:list=None,log=False,threads:int=6):
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
            

    thread_args = [[x]+args if args else [x] for x in iterable_divided]
    pool = ThreadPool(threads)
    results = pool.starmap(func,thread_args)
    pool.close()
    pool.join()
    if log:
        print(f'Threaded: Finished {func.__name__} in {time.time()-start_time} seconds')
    return results


def process_date(value:str):
    '''Process date string'''
    date = ''
    try:
        date = datetime.datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d')
    except Exception as e:
        pass
    return date

def process_date_utc(value:str):
    '''Process dateutc string'''
    date = ''
    try:
        date = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        pass
    return date

def process_mssql_value(value:str):
    '''Process value to be inserted in mssql db'''
    if value:
        value = f"{value}".replace("\'","\'\'")
    return value

def process_mssql_number(value:str,default:str='-1'):
    '''Process number to be inserted in mssql db'''
    number = default
    if f'{value}':
        number = f'{value}'.replace("\'","\'\'")
    if number.strip() in ['','None']:
        number = default
    return number

def process_mssql_bool(value:str,default:str='0'):
    '''Process bool to be inserted in mssql db'''
    bool = default
    if f'{value}':
        try:
            bool = f'{value}'.replace("\'","\'\'").lower()
            if bool == 'true':
                bool = '1'
            else:
                bool = '0'
        except Exception as e:
            bool = default
            pass
    return bool
    

def db_non_existent_players(players:list,db_handler:Db_handler):
    '''Returns list of players that are not in db'''
    where_statement = 'where idplayer in ('
    #remove duplicates in players list
    unique_players = {}
    for player in players:
        if player['wyId'] not in unique_players:
            unique_players[player['wyId']]= player

    # create where statement
    for player_id in unique_players:
        where_statement += f"'{player_id}',"
    where_statement = where_statement[:-1] + ')'

    # get players from db
    db_players = db_handler.select('player','*',where_statement)
    if db_players:
        db_players = [p[0] for p in db_players]

    # get non existent players
    non_existent_players = [p for p in unique_players.values() if p['wyId'] not in db_players]
    return non_existent_players


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
            'seasons':[],
            'custom_name' : None
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

def prepare_areas_insert(areas):
    '''Inserts area into db'''
    querys = []
    for area in areas:
        area_id = process_mssql_value(area['id'])
        area_name = process_mssql_value(area['name'])
        area_alpha3code = process_mssql_value(area['alpha3code'])

        values = f'''('{area_id}', '{area_name}', '{area_alpha3code}')'''
        querys.append(values)
    return querys

def populate_areas(db_handler:Db_handler):
    '''Populates areas table in db'''
    areas = get_areas()
    query_values = prepare_areas_insert(areas)
    parameters = ['idareas', 'name', 'alpha3code']
    key_parameters = ['idareas']
    db_handler.insert_or_update_many('area',query_values,key_parameters=key_parameters,parameters=parameters)




def populate_competitions(db_handler:Db_handler,competitions_id:list):
    '''Populates competitions table in db'''
    c_i = 0
    values = []
    for competition_id,competition_custom_name in competitions_id:
        print(f'Requesting competition {c_i}/{len(competitions_id)}')
        competition_info = get_competition_info(competition_id)
        if competition_info:
            wyId = process_mssql_value(competition_info['wyId'])
            name = process_mssql_value(competition_info['name'])
            area_id = process_mssql_value(competition_info['area']['id'])
            gender = process_mssql_value(competition_info['gender'])
            type = process_mssql_value(competition_info['type'])
            format = process_mssql_value(competition_info['format'])
            divisionLevel = process_mssql_value(competition_info['divisionLevel'])
            category = process_mssql_value(competition_info['category'])
            custom_name =process_mssql_value(competition_custom_name)

            values.append(f'''('{wyId}', '{name}', '{area_id}', '{gender}',\
                         '{type}', '{format}', '{divisionLevel}', '{category}', '{custom_name}')''')
            
        c_i += 1
    key_parameters = ['idcompetitions']
    parameters = ['idcompetitions','name','area','gender','type','format','divisionLevel','category','custom_name']

    db_handler.insert_or_update_many('competition',values,key_parameters=key_parameters,parameters=parameters)


def populate_competitions_seasons(db_handler:Db_handler,seasons_id:list):
    '''Populates seasons table in db'''
    s_i = 0
    values = []
    for season_id in seasons_id:
        print(f'Requesting season {s_i}/{len(seasons_id)}')
        season_info = get_season_info(season_id)
        if season_info:
            wyId = process_mssql_value(season_info['wyId'])
            startDate = process_date(season_info['startDate'])
            endDate = process_date(season_info['endDate'])
            name = process_mssql_value(season_info['name'])
            competitionId = process_mssql_value(season_info['competitionId'])

            values.append(f'''('{wyId}', '{startDate}', '{endDate}', '{name}', '{competitionId}')''')
        s_i += 1

    key_parameters = ['idcompetition_season']
    parameters = ['idcompetition_season','startDate','endDate','name','competition']
    db_handler.insert_or_update_many('competition_season',values,key_parameters=key_parameters,parameters=parameters)


def prepare_teams_insert(teams,season_id:int,round_id:int):
    '''Inserts team into db, as well as team_competition_season table'''

    querys = []
    for team in teams:
        team_info = team['team']
        if team_info:
            wyId = process_mssql_value(team_info['wyId'])
            name = process_mssql_value(team_info['name'])
            officialName = process_mssql_value(team_info['officialName'])
            imageDataURL = process_mssql_value(team_info['imageDataURL'])
            gender = process_mssql_value(team_info['gender'])
            type = process_mssql_value(team_info['type'])
            city = process_mssql_value(team_info['city'])
            category = process_mssql_value(team_info['category'])
            area_id = process_mssql_value(team_info['area']['id'])

            values = f'''('{wyId}', '{name}', '{officialName}', '{imageDataURL}', '{gender}', '{type}',\
                        '{city}', '{category}', '{area_id}')'''
            querys.append(('team',values,wyId))

            totalDraws = process_mssql_number(team['gameDraw'])
            totalGoalsAgainst = process_mssql_number(team['goalAgainst'])
            totalGoalsFor = process_mssql_number(team['goalPro'])
            totalLosses = process_mssql_number(team['gameLost'])
            totalPlayed = process_mssql_number(team['gameTotal'])
            totalPoints = process_mssql_number(team['points'])
            totalWins = process_mssql_number(team['gameWon'])
            rank = process_mssql_number(team['rank'])

            values_tcsr = f'''('{round_id}', '{wyId}','{totalDraws}','{totalGoalsAgainst}','{totalGoalsFor}','{totalLosses}',\
                        '{totalPlayed}','{totalPoints}','{totalWins}','{rank}')'''
            
            values_tcs = f'''('{season_id}', '{wyId}')'''
            querys.append(('team_competition_season_round',values_tcsr))
            querys.append(('team_competition_season',values_tcs,wyId))
    return querys



def populate_teams(db_handler:Db_handler,season_id:int):
    '''Populates teams table in db, as well as team_competition_season table'''    
    season_rounds = get_season_career(season_id)

    rounds_queries = []
    teams_queries = []

    for season_round in season_rounds:
        round = season_round['round']
        startDate = process_date(round['startDate'])
        endDate = process_date(round['endDate'])
        name = process_mssql_value(round['name'])
        round_id = process_mssql_value(round['wyId'])
        values = f'''('{round_id}','{season_id}','{startDate}', '{endDate}', '{name}' )'''
        rounds_queries.append(values)
        #process round
        groups = season_round['groups']
        teams = []
        for group in groups:
            teams_group = group['teams']
            teams += teams_group
        
        result = run_threaded_for(prepare_teams_insert,teams,log=True,args=[season_id,round['wyId']])
        teams_queries += [query for query_list in result for query in query_list]
    
    team_query_values = {} # dict to remove duplicates
    team_competition_season_round_query_values = []
    team_competition_season_query_values = {} # dict to remove duplicates
    # separate querys
    for query in teams_queries:
        if query[0] == 'team':
            team_query_values[query[2]] = query[1]
        elif query[0] == 'team_competition_season':
            team_competition_season_query_values[query[2]] = query[1]
        elif query[0] == 'team_competition_season_round':
            team_competition_season_round_query_values.append(query[1])

    #insert rounds
    rounds_key_parameters = ['idcompetition_season_round']
    parameters = ['idcompetition_season_round','competition_season','startDate','endDate','name']
    db_handler.insert_or_update_many('competition_season_round',rounds_queries,key_parameters=rounds_key_parameters,parameters=parameters)
    
    #insert teams
    team_query_values = [value for value in team_query_values.values()]
    team_key_parameters = ['idteam']
    team_parameters = ['idteam','name','official_name','icon','gender','type','city','category','area']
    db_handler.insert_or_update_many('team',team_query_values,key_parameters=team_key_parameters,parameters=team_parameters)

    #insert teams competition season
    team_competition_season_query_values = [value for value in team_competition_season_query_values.values()]
    team_competition_season_key_parameters = ['competition_season','team']
    team_competition_season_parameters = ['competition_season','team']
    db_handler.insert_or_update_many('team_competition_season',team_competition_season_query_values,key_parameters=team_competition_season_key_parameters,parameters=team_competition_season_parameters)
    
    #insert teams competition season rounds
    team_competition_season_round_key_parameters = ['competition_season_round','team']
    team_competition_season_round_parameters = ['competition_season_round','team','totalDraws','totalGoalsAgainst','totalGoalsFor','totalLosses','totalPlayed','totalPoints','totalWins','rank']
    db_handler.insert_or_update_many('team_competition_season_round',team_competition_season_round_query_values,key_parameters=team_competition_season_round_key_parameters,parameters=team_competition_season_round_parameters)

def prepare_players_insert(players,season_id,player_advanced_stats:bool=False):
    querys = []
    for player in players:
        contractInfo = get_player_contract_info(player['wyId'])
        contractExpiration = contractInfo['contractExpiration']
        player_agencies = ""
        if 'agencies' in contractInfo and len(contractInfo['agencies']) > 0:
            player_agencies = contractInfo['agencies'][0]
            for agencie in contractInfo['agencies'][1:]:
                player_agencies+= ', ' + agencie

        player_name = player['firstName'].strip() + ' ' + player['middleName'].strip() + ' ' + player['lastName'].strip()
        player_name = process_mssql_value(player_name)
        wyId = process_mssql_value(player['wyId'])
        shortName = process_mssql_value(player['shortName'])
        birthArea = process_mssql_value(player['birthArea']['id'])
        birthDate = process_date(player['birthDate'])
        imageDataURL = process_mssql_value(player['imageDataURL'])
        foot = process_mssql_value(player['foot'])
        height = process_mssql_value(player['height'])
        weight = process_mssql_value(player['weight'])
        status = process_mssql_value(player['status'])
        gender = process_mssql_value(player['gender'])
        role_code2 = process_mssql_value(player['role']['code2'])
        role_code3 = process_mssql_value(player['role']['code3'])
        role_name = process_mssql_value(player['role']['name'])
        contractExpiration = process_date(contractExpiration)
        player_agencies = process_mssql_value(player_agencies)
        current_team = process_mssql_number(player['currentTeamId'])

        values = f'''('{wyId}', '{player_name}', '{shortName}', '{birthArea}', \
                    '{birthDate}', '{imageDataURL}', '{foot}',\
                    '{height}','{weight}','{status}','{gender}',\
                    '{role_code2}', '{role_code3}', '{role_name}'\
                    ,'{contractExpiration}','{player_agencies}','{current_team}')'''
        querys.append(('player',values))

        # get player advanced stats
        if player_advanced_stats:
            career = get_player_career(player['wyId'])
            entries = get_season_career_entries(career,int(season_id))
            # populate career table
            for entry in entries:
                season = process_mssql_value(entry['seasonId'])
                team = process_mssql_value(entry['teamId'])
                competition = process_mssql_value(entry['competitionId'])
                appearances = process_mssql_number(entry['appearances'])
                goal = process_mssql_number(entry['goal'])
                minutesPlayed = process_mssql_number(entry['minutesPlayed'])
                penalties = process_mssql_number(entry['penalties'])
                redCards = process_mssql_number(entry['redCards'])
                shirtNumber = process_mssql_number(entry['shirtNumber'])
                substituteIn = process_mssql_number(entry['substituteIn'])
                substituteOnBench = process_mssql_number(entry['substituteOnBench'])
                substituteOut = process_mssql_number(entry['substituteOut'])
                yellowCard = process_mssql_number(entry['yellowCard'])

                values = f'''SELECT '{wyId}', idteam_competition_season, '{appearances}','{goal}','{minutesPlayed}',\
                            '{penalties}','{redCards}','{shirtNumber}','{substituteIn}','{substituteOnBench}',\
                            '{substituteOut}','{yellowCard}','{team}','{season}' 
                            FROM [scouting].[team_competition_season] 
                            WHERE [team]='{team}' AND [competition_season]='{season}' '''
                querys.append(('career_entry',values))

                advanced_stats = get_player_advanced_stats(player['wyId'],competition,season)
                if advanced_stats:
                    # populate positions table
                    positions = advanced_stats['positions']
                    for position in positions:
                        position_percent = process_mssql_value(position['percent'])
                        position_code = process_mssql_value(position['position']['code'])
                        position_name = process_mssql_value(position['position']['name'])

                        values = f'''SELECT '{wyId}', '{position_percent}','{position_code}', '{position_name}',idteam_competition_season \
                                    FROM [scouting].[team_competition_season] WHERE [team]='{team}' AND [competition_season]='{season}' '''
                        querys.append(('player_positions',values))
        pbar_players.update(1)
    return querys
        
    

def populate_players(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates players table in db'''
    print(f'Populating players from season {season_id}')
    players = get_season_players(season_id)
    pbar_players.reset(total=len(players))
    result = run_threaded_for(prepare_players_insert,players,log=True,args=[season_id,player_advanced_stats],threads=12)
    querys = [query for query_list in result for query in query_list]
    player_querys_values = []
    player_positions_querys_values = []
    career_entry_querys_values = []
    # separate querys
    for query in querys:
        if query[0] == 'player':
            player_querys_values.append(query[1])
        elif query[0] == 'player_positions':
            player_positions_querys_values.append(query[1])
        elif query[0] == 'career_entry':
            career_entry_querys_values.append(query[1])

    player_key_parameters = ['idplayer']
    player_parameters = ['idplayer','name','short_name','birth_area','birth_date','image','foot','height','weight',
                         'status','gender','role_code2','role_code3','role_name','contract_expiration','contract_agency','current_team']
    db_handler.insert_or_update_many('player',player_querys_values,key_parameters=player_key_parameters,parameters=player_parameters)

    career_entry_key_parameters = ['player','team_competition_season']
    career_entry_parameters = ['player','team_competition_season','appearances','goal','minutesPlayed','penalties',
                               'redCards','shirtNumber','substituteIn','substituteOnBench','substituteOut','yellowCard','team','competition_season']
    db_handler.insert_or_update_many('career_entry',career_entry_querys_values,key_parameters=career_entry_key_parameters,parameters=career_entry_parameters,delimiter=' UNION ALL ')
    
    if player_advanced_stats:
        player_positions_key_parameters = ['player','code','team_competition_season']
        player_positions_parameters = ['player','percent','code','name','team_competition_season']
        db_handler.insert_or_update_many('player_positions',player_positions_querys_values,key_parameters=player_positions_key_parameters,parameters=player_positions_parameters,delimiter=' UNION ALL ')


def prepare_match_players_stats_insert(match:int,players:bool=False):
    '''Prepare values for player_match_stats table in db'''
    querys = []
    players_list = []
    match_players_stats = get_match_players_stats(match,players=players)
    for player_stats in match_players_stats:
        player = process_mssql_value(player_stats['playerId'])
        offensive_duels = process_mssql_number(player_stats['total']['offensiveDuels'])
        progressive_passes = process_mssql_number(player_stats['total']['progressivePasses'])
        forward_passes = process_mssql_number(player_stats['total']['forwardPasses'])
        crosses = process_mssql_number(player_stats['total']['crosses'])
        key_passes = process_mssql_number(player_stats['total']['keyPasses'])
        defensive_duels = process_mssql_number(player_stats['total']['defensiveDuels'])
        interceptions = process_mssql_number(player_stats['total']['interceptions'])
        recoveries = process_mssql_number(player_stats['total']['recoveries'])
        successful_passes = process_mssql_number(player_stats['percent']['successfulPasses'])
        long_passes = process_mssql_number(player_stats['total']['longPasses'])
        aerial_duels = process_mssql_number(player_stats['total']['aerialDuels'])
        losses = process_mssql_number(player_stats['total']['losses'])
        own_half_losses = process_mssql_number(player_stats['total']['ownHalfLosses'])
        goal_kicks = process_mssql_number(player_stats['total']['goalKicks'])
        received_pass = process_mssql_number(player_stats['total']['receivedPass'])
        dribbles = process_mssql_number(player_stats['total']['dribbles'])
        touch_in_box = process_mssql_number(player_stats['total']['touchInBox'])
        opponent_half_recoveries = process_mssql_number(player_stats['total']['opponentHalfRecoveries'])

        values = f'''('{match}', '{player}', '{offensive_duels}', '{progressive_passes}', '{forward_passes}',\
                     '{crosses}', '{key_passes}', '{defensive_duels}', '{interceptions}', '{recoveries}',\
                     '{successful_passes}', '{long_passes}', '{aerial_duels}', '{losses}', '{own_half_losses}',\
                     '{goal_kicks}', '{received_pass}', '{dribbles}', '{touch_in_box}', '{opponent_half_recoveries}')'''

        querys.append(('player_match_stats',values))
        if players:
            if player_stats['player']:
                players_list.append(player_stats['player'])
            # inconsistency (player is not registered in API), remove last query
            else:
                querys.pop()
    if players:
        return querys,players_list
    return querys
    


def prepare_match_formation_insert(match:int,match_team_info:dict):
    '''Prepare values for match_formation table in db'''
    querys = []
    for team,team_info in match_team_info.items():
        formation = team_info['formation']
        if formation:
            substitutes = {}
            # get team substitutions
            for player in formation['substitutions']:
                substitutes[player['playerIn']] = {}
                substitutes[player['playerIn']]['playerIn'] = process_mssql_value(player['playerIn'])
                substitutes[player['playerIn']]['playerOut'] = process_mssql_value(player['playerOut'])
                substitutes[player['playerIn']]['minute'] = process_mssql_number(player['minute'])
                values = f'''('{match}', '{substitutes[player['playerIn']]['playerIn']}', \
                            '{substitutes[player['playerIn']]['playerOut']}', '{team_info['teamId']}',\
                            '{substitutes[player['playerIn']]['minute']}')'''
                querys.append(('match_substitution',values))
            # team initial lineup
            for player in formation['lineup']:
                player_id = process_mssql_value(player['playerId'])
                assists = process_mssql_number(player['assists'])
                goals = process_mssql_number(player['goals'])
                own_goals = process_mssql_number(player['ownGoals'])
                red_cards = process_mssql_number(player['redCards'])
                shirt_number = process_mssql_value(player['shirtNumber'])
                yellow_cards = process_mssql_number(player['yellowCards'])
                minute = 0
                type = 'lineup'
                values = f'''('{match}', '{player_id}', '{assists}', '{goals}', '{own_goals}', '{red_cards}', \
                            '{shirt_number}', '{yellow_cards}', '{minute}', '{team_info['teamId']}', '{type}')'''
                querys.append(('match_formation',values))
            # team bench
            for player in formation['bench']:
                player_id = process_mssql_value(player['playerId'])
                assists = process_mssql_number(player['assists'])
                goals = process_mssql_number(player['goals'])
                own_goals = process_mssql_number(player['ownGoals'])
                red_cards = process_mssql_number(player['redCards'])
                shirt_number = process_mssql_number(player['shirtNumber'])
                yellow_cards = process_mssql_number(player['yellowCards'])
                minute = 0
                type = 'bench'
                if player_id in substitutes:
                    minute = substitutes[player_id]['minute']
                    type = 'substitution'
                values = f'''('{match}', '{player_id}', '{assists}', '{goals}', '{own_goals}', '{red_cards}',\
                             '{shirt_number}', '{yellow_cards}', '{minute}', '{team_info['teamId']}', '{type}')'''
                querys.append(('match_formation',values))
    return querys




def prepare_matches_insert(matches,db_handler:Db_handler,season_id,player_advanced_stats:bool=False):
    querys = []
    matches_players_list = []
    for match in matches:
        match_info = get_match_info(match['matchId'])
        # get match basic info
        if match_info:
            wyId = process_mssql_value(match_info['wyId'])
            seasonId = process_mssql_value(match_info['seasonId'])
            roundId = process_mssql_value(match_info['roundId'])
            home_team = process_mssql_value(match_info['teamsData']['home']['teamId'])
            home_score = process_mssql_value(match_info['teamsData']['home']['score'])
            away_team = process_mssql_value(match_info['teamsData']['away']['teamId'])
            away_score = process_mssql_value(match_info['teamsData']['away']['score'])
            dateutc = process_date_utc(match_info['dateutc'])
            winner = process_mssql_value(match_info['winner'])


            values = f'''('{wyId}','{seasonId}','{roundId}', '{home_team}', '{away_team}', '{dateutc}',\
            '{home_score}','{away_score}', '{winner}')'''

            querys.append(('match',values))

            # get match players and populate player table with non existent players to avoid errors (because of api inconsistency)
            for team in match_info['teamsData']:
                if match_info['teamsData'][team]['formation']:
                    for player in match_info['teamsData'][team]['formation']['lineup']:
                        matches_players_list.append(player['player'])
                    for player in match_info['teamsData'][team]['formation']['bench']:
                        matches_players_list.append(player['player'])


            match_events = get_match_events(match['matchId'])
            match_lineups = get_match_lineups(match['matchId'])

            # get team's match formation
            querys += prepare_match_formation_insert(match['matchId'],match_info['teamsData'])
            
            # get match lineups
            if match_lineups:
                teams = [x for x in match_lineups if x != "teams"]
                for team in teams:
                    lineup_info = match_lineups[team]
                    for part,times in lineup_info.items():
                        for time,lineups in times.items():
                            for lineup in lineups:
                                scheme = process_mssql_value(lineups[lineup]['scheme'])
                                values = f'''('{match['matchId']}', '{team}', '{part}', '{time}','{scheme}')'''
                                querys.append(('match_lineup',values))
                                players = lineups[lineup]['players']
                                # players positions in lineup
                                for playerdict in players:
                                    for playerId in playerdict:
                                        position = process_mssql_value(playerdict[playerId]['position'])
                                        values = f'''SELECT match_lineup_id, '{playerId}','{position}' 
                                                    FROM [scouting].[match_lineup] 
                                                    WHERE [match]='{match['matchId']}' AND [team]='{team}' AND [period]='{part}' AND [second]='{time}' '''
                                        querys.append(('match_lineup_player_position',values))

            # get match advanced stats for each player
            if player_advanced_stats:
                query_list,players_list = prepare_match_players_stats_insert(match['matchId'],players=True)
                querys += query_list
                # get match players for populate (because of api inconsistency)
                matches_players_list += players_list
                

            # # get match events
            for event in match_events:
                id = process_mssql_value(event['id'])
                matchid = process_mssql_value(event['matchId'])
                player = process_mssql_value(event['player']['id'])
                matchPeriod = process_mssql_value(event['matchPeriod'])
                if event['location'] != None:
                    location_x = process_mssql_value(event['location']['x'])
                    location_y = process_mssql_value(event['location']['y'])
                else:
                    location_x = -1 #TODO: ver melhor isto
                    location_y = -1 #TODO: ver melhor isto
                minute = process_mssql_number(event['minute'])
                second = process_mssql_number(event['second'])
                if event['pass'] != None:
                    accurate = process_mssql_bool(event['pass']['accurate'])
                    recipient = process_mssql_value(event['pass']['recipient']['id'])
                    endlocation_x = process_mssql_number(event['pass']['endLocation']['x'])
                    endlocation_y = process_mssql_number(event['pass']['endLocation']['y'])
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}'
                    , '{accurate}', '{recipient}', '{endlocation_x}', '{endlocation_y}')'''
                    querys.append(('match_event_pass',values))

                elif event['shot'] != None:
                    isGoal = process_mssql_bool(event['shot']['isGoal'])
                    onTarget = process_mssql_bool(event['shot']['onTarget'])
                    xg = process_mssql_number(event['shot']['xg'])
                    postShotXg = process_mssql_number(event['shot']['postShotXg'])
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}'
                    , '{isGoal}', '{onTarget}', '{xg}', '{postShotXg}')'''
                    querys.append(('match_event_shot',values))

                elif event['infraction'] != None and (event['infraction']['yellowCard'] or event['infraction']['redCard']):
                    yellowCard = process_mssql_bool(event['infraction']['yellowCard'])
                    redCard = process_mssql_bool(event['infraction']['redCard'])
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}'
                    , '{yellowCard}', '{redCard}')'''
                    querys.append(('match_event_infraction',values))

                elif event['carry'] != None:    
                    endlocation_x = process_mssql_number(event['carry']['endLocation']['x'])
                    endlocation_y = process_mssql_number(event['carry']['endLocation']['y'])
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}'
                    , '{endlocation_x}', '{endlocation_y}')'''
                    querys.append(('match_event_carry',values))

                else:
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}')'''
                    querys.append(('match_event_other',values))
        pbar_matches.update(1)
    # prepare insert of non existent players
    matches_players_list = db_non_existent_players(matches_players_list,db_handler)
    results = prepare_players_insert(matches_players_list,season_id,player_advanced_stats=player_advanced_stats)
    querys += results
    return querys
        



def populate_matches(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates matches table in db, gathering matches from given season\n
    Can gather advanced stats from players in each match'''
    print(f'Populating matches from season {season_id}')
    matches = get_season_matches(season_id)
    pbar_matches.reset(total=len(matches))
    pbar_players.disable = True
    result = run_threaded_for(prepare_matches_insert,matches,log=True,args=[db_handler,season_id,player_advanced_stats],threads=10)
    pbar_players.disable = False
    pbar_matches.refresh()
    pbar_matches.reset()
    pbar_players.clear()
    querys = [query for query_list in result for query in query_list]
    match_query_values = []
    player_query_values = []
    player_match_stats_query_values = []
    match_lineup_values = []
    match_lineup_player_position_values = []
    match_formation_values = []
    match_substitution_values = []
    match_events_values = {
        "pass" : [],
        "shot" : [],
        "infraction" : [],
        "carry" : [],
        "other" : []
    }
    # separate querys
    for query in querys:
        if query[0] == 'match':
            match_query_values.append(query[1])
        elif query[0] == 'player':
            player_query_values.append(query[1])
        elif query[0] == 'player_match_stats':
            player_match_stats_query_values.append(query[1])
        elif query[0] == 'match_lineup':
            match_lineup_values.append(query[1])
        elif query[0] == 'match_lineup_player_position':
            match_lineup_player_position_values.append(query[1])
        elif query[0] == 'match_formation':
            match_formation_values.append(query[1])
        elif query[0] == 'match_substitution':
            match_substitution_values.append(query[1])
        elif query[0] == 'match_event_pass':
            match_events_values['pass'].append(query[1])
        elif query[0] == 'match_event_shot':
            match_events_values['shot'].append(query[1])
        elif query[0] == 'match_event_infraction':
            match_events_values['infraction'].append(query[1])
        elif query[0] == 'match_event_carry':
            match_events_values['carry'].append(query[1])
        elif query[0] == 'match_event_other':
            match_events_values['other'].append(query[1])

    # # match table
    match_key_parameters = ['idmatch']
    match_parameters = ['idmatch', 'competition_season','round', 'home_team', 'away_team', 'date', 'home_score', 'away_score', 'winner']
    db_handler.insert_or_update_many('match',match_query_values,key_parameters=match_key_parameters,parameters=match_parameters)

    # player table
    player_key_parameters = ['idplayer']
    player_parameters = ['idplayer','name','short_name','birth_area','birth_date','image','foot','height','weight',
                         'status','gender','role_code2','role_code3','role_name','contract_expiration','contract_agency','current_team']
    db_handler.insert_or_update_many('player',player_query_values,key_parameters=player_key_parameters,parameters=player_parameters)
                         

    if player_advanced_stats:
        # player_match_stats table
        player_match_stats_key_parameters = ['match', 'player']
        player_match_stats_parameters = ['match', 'player', 'offensiveDuels', 'progressivePasses', 'forwardPasses', 
                                         'crosses', 'keyPasses', 'defensiveDuels', 'interceptions', 'recoveries',
                                        'successfulPasses', 'longPasses', 'aerialDuels', 'losses', 'ownHalfLosses', 
                                        'goalKicks', 'receivedPass', 'dribbles', 'touchInBox', 'opponentHalfRecoveries']
        db_handler.insert_or_update_many('player_match_stats',player_match_stats_query_values,key_parameters=player_match_stats_key_parameters,parameters=player_match_stats_parameters)

    # match_lineup table
    match_lineup_key_parameters = ['match', 'team', 'period', 'second']
    match_lineup_parameters = ['match', 'team', 'period', 'second', 'lineup']
    db_handler.insert_or_update_many('match_lineup',match_lineup_values,key_parameters=match_lineup_key_parameters,parameters=match_lineup_parameters)

    # match_lineup_player_position table
    match_lineup_player_position_key_parameters = ['match_lineup_id', 'player']
    match_lineup_player_position_parameters = ['match_lineup_id', 'player', 'position']
    db_handler.insert_or_update_many('match_lineup_player_position',match_lineup_player_position_values,key_parameters=match_lineup_player_position_key_parameters,
                                     parameters=match_lineup_player_position_parameters,delimiter=' UNION ALL ')

    # match_formation table
    match_formation_key_parameters = ['match', 'player']
    match_formation_parameters = ['match', 'player', 'assists', 'goals', 'ownGoals', 'redCards', 'shirtNumber', 'yellowCards', 'minute', 'team', 'type']
    db_handler.insert_or_update_many('match_formation',match_formation_values,key_parameters=match_formation_key_parameters,parameters=match_formation_parameters)

    # match_substitution table
    match_substitution_key_parameters = ['match', 'playerIn', 'playerOut']
    match_substitution_parameters = ['match', 'playerIn', 'playerOut', 'team', 'minute']
    db_handler.insert_or_update_many('match_substitution',match_substitution_values,key_parameters=match_substitution_key_parameters,parameters=match_substitution_parameters,batch_size=3000)

    # match_event table
    # other
    match_event_other_key_parameters = ['idmatch_event']
    match_event_other_parameters = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y', 'minute', 'second']
    db_handler.insert_or_update_many('match_event_other', match_events_values['other'], key_parameters=match_event_other_key_parameters, parameters=match_event_other_parameters,batch_size=3000)
    # pass
    match_event_pass_key_parameters = ['idmatch_event']
    match_event_pass_parameters = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y', 'minute', 'second', 'accurate', 'recipient', 'endlocation_x', 'endlocation_y']
    db_handler.insert_or_update_many('match_event_pass', match_events_values['pass'], key_parameters=match_event_pass_key_parameters, parameters=match_event_pass_parameters,batch_size=3000)
    # shot
    match_event_shot_key_parameters = ['idmatch_event']
    match_event_shot_parameters = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y', 'minute', 'second', 'isGoal', 'onTarget', 'xg', 'postShotXg']
    db_handler.insert_or_update_many('match_event_shot', match_events_values['shot'], key_parameters=match_event_shot_key_parameters, parameters=match_event_shot_parameters,batch_size=3000)
    # carry
    match_event_carry_key_parameters = ['idmatch_event']
    match_event_carry_parameters = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y', 'minute', 'second', 'endlocation_x', 'endlocation_y']
    db_handler.insert_or_update_many('match_event_carry', match_events_values['carry'], key_parameters=match_event_carry_key_parameters, parameters=match_event_carry_parameters,batch_size=3000)
    # infraction
    match_event_infraction_key_parameters = ['idmatch_event']
    match_event_infraction_parameters = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y', 'minute', 'second', 'yellowCard', 'redCard']
    db_handler.insert_or_update_many('match_event_infraction', match_events_values['infraction'], key_parameters=match_event_infraction_key_parameters, parameters=match_event_infraction_parameters,batch_size=3000)
    

        


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
                competitions_id = [(c['wyId'],c['custom_name']) for c in competitions_info]
                # populate competitions
                populate_competitions(db_handler,competitions_id)

                # populate seasons
                seasons_id = [s for c in competitions_info for s in c['seasons']]
                populate_competitions_seasons(db_handler,seasons_id)

                s_i = 1
                # populate teams, players, matches and stats
                for s_id in seasons_id:
                    print(f'Extracting info from season {s_id} | {s_i}/{len(seasons_id)}')
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



                        