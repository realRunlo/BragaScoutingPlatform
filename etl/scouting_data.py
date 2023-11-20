import json
import os
import argparse
import random
import threading
import time
import logging
import traceback
from db import Db_handler
from multiprocessing.pool import ThreadPool
from utils import *
from api_handler import *
from tqdm import tqdm
from consts import *

pbar_competitions = tqdm()
pbar_competitions.desc = 'Competitions'
pbar_seasons = tqdm()
pbar_seasons.desc = 'Seasons'
pbar_teams = tqdm()
pbar_teams.desc = 'Teams'
pbar_players = tqdm()
pbar_players.desc = 'Players'
pbar_matches = tqdm()
pbar_matches.desc = 'Matches'

            


def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--db_config','-dbc'            ,type=str, nargs=1,required=True                                , help='Db config json file path')
    parser.add_argument('--full_info','-fi'             ,type=str, nargs=1                                              , help="Request all info from API, according to json file provided")
    parser.add_argument('--log','-l'                    ,action='store_true'                                            , help="Activate logging, with optional log file path")
    return parser.parse_args()



def run_threaded_for(func,iterable:list, args:list=None,log=False,threads:int=6):
    '''Runs a function for each value in iterable'''
    if log:
        start_time = time.time()
        print(f'Threaded: Running {func.__name__} to gather info from {len(iterable)} items ')
    
    # limit threads during working hours
    if working_hours():
        threads = 1

    iterable_divided = [None]*threads
    max_slice_size = len(iterable)//threads
    # divide work between threads
    for i in range(threads):
        if i == threads-1:
            iterable_divided[i] = iterable[i*max_slice_size:]
        else:
            iterable_divided[i] = iterable[i*max_slice_size:(i+1)*max_slice_size]
            

    thread_args = [[x]+args if args else [x] for x in iterable_divided]
    try:
        pool = ThreadPool(threads)
        results = pool.starmap(func,thread_args)
        pool.close()
        pool.join()
        if log:
            print(f'Threaded: Finished {func.__name__} in {time.time()-start_time} seconds')
    except Exception as e:
        print(f'Threaded: Error running {func.__name__}')
        print(traceback.format_exc())
        print(e)
        pool.terminate()
        raise e
    return results


def process_date(value:str):
    '''Process date string'''
    date = 'NULL'
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
    

def db_non_existent_players(players:list):
    '''Returns list of players that are not in db'''
    global db_connection

    non_existent_players = []
    where_statement = 'where idplayer in ('
    #remove duplicates in players list
    unique_players = {}
    for player in players:
        if player['wyId'] not in unique_players:
            unique_players[player['wyId']]= player
    if unique_players:
        # create where statement
        for player_id in unique_players:
            where_statement += f"'{player_id}',"
        where_statement = where_statement[:-1] + ')'

        # get players from db
        db_players = db_connection.select('player','*',where_statement)
        if db_players:
            db_players = [p[0] for p in db_players]
            # get non existent players
            non_existent_players = [p for p in unique_players.values() if p['wyId'] not in db_players]
            
    return non_existent_players


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
    # append null area
    areas.append({'id':0,'name':None,'alpha3code':None})
    query_values = prepare_areas_insert(areas)
    db_handler.insert_or_update_many('area',query_values,key_parameters=area_key_parameters,parameters=area_parameters)



def prepare_competitions_insert(competitions_id:list):
    '''Prepare competitions values for insert in db'''
    file_name = f'{tmp_folder}/competitions_names_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    values_file = open(file_name,'w',encoding='utf-8')
    for competition_id,competition_custom_name in competitions_id:
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

            values_file.write(f'''('{wyId}', '{name}', '{area_id}', '{gender}',\
                         '{type}', '{format}', '{divisionLevel}', '{category}', '{custom_name}')''')
            values_file.write(file_delimiter)
        pbar_competitions.update(1)
    values_file.close()
    return file_name



def populate_competitions(db_handler:Db_handler,competitions_id:list):
    '''Populates competitions table in db'''
    pbar_competitions.reset(total=len(competitions_id))
    results = run_threaded_for(prepare_competitions_insert,competitions_id,log=True)
    values_files = [file for file in results]

    for file in values_files:
        db_handler.request_insert_or_update_many('competition',file,key_parameters=competition_key_parameters,parameters=competition_parameters)


def prepare_competitions_seasons_insert(competitions_seasons_id:list):
    '''Prepare seasons values for insert in db'''
    file_name = f'{tmp_folder}/competitions_seasons_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    values_file = open(file_name,'w',encoding='utf-8')

    for competition_season in competitions_seasons_id:
        competition_season_info = get_season_info(competition_season)

        competition_season_id = process_mssql_value(competition_season_info['wyId'])
        competition_season_startDate = process_date(competition_season_info['startDate'])
        competition_season_startDate = f'\'{competition_season_startDate}\'' if competition_season_startDate != 'NULL' else 'NULL'
        competition_season_endDate = process_date(competition_season_info['endDate'])
        competition_season_endDate = f'\'{competition_season_endDate}\'' if competition_season_endDate != 'NULL' else 'NULL'
        competition_season_name = process_mssql_value(competition_season_info['name'])
        competition_season_competitionId = process_mssql_value(competition_season_info['competitionId'])

        values = f'''('{competition_season_id}', {competition_season_startDate}, {competition_season_endDate}, '{competition_season_name}', '{competition_season_competitionId}')'''
        values_file.write(values)
        values_file.write(file_delimiter)
        pbar_seasons.update(1)
    values_file.close()
    return file_name


def populate_competitions_seasons(db_handler:Db_handler,seasons_id:list):
    '''Populates seasons table in db'''
    pbar_seasons.reset(total=len(seasons_id))
    results = run_threaded_for(prepare_competitions_seasons_insert,seasons_id,log=True)
    values_files = [file for file in results]
    for file in values_files:
        db_handler.request_insert_or_update_many('competition_season',file,key_parameters=competition_season_key_parameters,parameters=competition_season_parameters)


def prepare_teams_insert(teams,season_id:int,round_id:int):
    '''Inserts team into db, as well as team_competition_season table'''
    # prepare values files
    team_values_file_name = f'{tmp_folder}/teams_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    team_values_file = open(team_values_file_name,'w',encoding='utf-8')
    team_competition_season_values_file_name = f'{tmp_folder}/team_competition_season_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    team_competition_season_values_file = open(team_competition_season_values_file_name,'w',encoding='utf-8')
    team_competition_season_round_values_file_name = f'{tmp_folder}/team_competition_season_round_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    team_competition_season_round_values_file = open(team_competition_season_round_values_file_name,'w',encoding='utf-8')
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
            team_values_file.write(values)
            team_values_file.write(file_delimiter)

            totalDraws = process_mssql_number(team['gameDraw'])
            totalGoalsAgainst = process_mssql_number(team['goalAgainst'])
            totalGoalsFor = process_mssql_number(team['goalPro'])
            totalLosses = process_mssql_number(team['gameLost'])
            totalPlayed = process_mssql_number(team['gameTotal'])
            totalPoints = process_mssql_number(team['points'])
            totalWins = process_mssql_number(team['gameWon'])
            rank = process_mssql_number(team['rank'])
            group_id = process_mssql_value(team['groupId'])

            values_tcsr = f'''('{round_id}', '{wyId}','{totalDraws}','{totalGoalsAgainst}','{totalGoalsFor}','{totalLosses}',\
                        '{totalPlayed}','{totalPoints}','{totalWins}','{rank}', {group_id})'''
            team_competition_season_values_file.write(values_tcsr)
            team_competition_season_values_file.write(file_delimiter)
            
            values_tcs = f'''('{season_id}', '{wyId}')'''
            team_competition_season_round_values_file.write(values_tcs)
            team_competition_season_round_values_file.write(file_delimiter)
        pbar_teams.update(1)
    
    team_values_file.close()
    team_competition_season_values_file.close()
    team_competition_season_round_values_file.close()
    return [(team_values_file_name,'team'),(team_competition_season_values_file_name,'team_competition_season'),(team_competition_season_round_values_file_name,'team_competition_season_round')]



def populate_teams(db_handler:Db_handler,season_id:int):
    '''Populates teams table in db, as well as team_competition_season table'''    
    season_rounds = get_season_career(season_id)

    # values files
    rounds_values_file_name = f'{tmp_folder}/rounds_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    rounds_values_file = open(rounds_values_file_name,'w',encoding='utf-8')
    groups_values_file_name = f'{tmp_folder}/groups_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    groups_values_file = open(groups_values_file_name,'w',encoding='utf-8')

    # teams info files list
    teams_files = []

    # update team pbar
    teams = []
    for season_round in season_rounds:
        groups = season_round['groups']
        for group in groups:
            teams_group = group['teams']
            teams += teams_group
    pbar_teams.reset(total=len(teams))

    # iterate over rounds
    for season_round in season_rounds:
        #process round
        round = season_round['round']
        round_id = process_mssql_value(round['wyId'])
        startDate = process_date(round['startDate'])
        startDate = f'\'{startDate}\'' if startDate != 'NULL' else 'NULL'
        endDate = process_date(round['endDate'])
        endDate = f'\'{endDate}\'' if endDate != 'NULL' else 'NULL'
        name = process_mssql_value(round['name'])
        type = process_mssql_value(round['type'])
        values = f'''('{round_id}','{season_id}',{startDate}, {endDate}, '{name}', '{type}' )'''
        rounds_values_file.write(values)
        rounds_values_file.write(file_delimiter)
        # process round's teams
        groups = season_round['groups']
        teams = []
        for group in groups:
            teams_group = group['teams']
            teams += teams_group
            # process group
            if teams_group:
                t = teams_group[0]
                group_id = process_mssql_value(t['groupId'])
                group_name = process_mssql_value(t['groupName'])
                values = f'''('{group_id}','{round_id}','{group_name}')'''
                groups_values_file.write(values)
                groups_values_file.write(file_delimiter)
        
        result = run_threaded_for(prepare_teams_insert,teams,log=True,args=[season_id,round['wyId']])
        teams_files += [file for files_list in result for file in files_list]

    # close rounds file
    rounds_values_file.close()
    
    team_values_files = []
    team_competition_season_round_values_files = []
    team_competition_season_values_files = []
    # separate files
    for file,type in teams_files:
        if type == 'team':
            team_values_files.append(file)
        elif type == 'team_competition_season':
            team_competition_season_round_values_files.append(file)
        elif type == 'team_competition_season_round':
            team_competition_season_values_files.append(file)

    #insert rounds
    db_handler.request_insert_or_update_many('competition_season_round',rounds_values_file_name,key_parameters=competition_season_round_key_parameters,parameters=competition_season_round_parameters)

    #insert groups
    db_handler.request_insert_or_update_many('competition_season_round_group',groups_values_file_name,key_parameters=competition_season_round_group_key_parameters,parameters=competition_season_round_group_parameters)
    
    #insert teams
    for file in team_values_files:
        db_handler.request_insert_or_update_many('team',file,key_parameters=team_key_parameters,parameters=team_parameters)

    #insert teams competition season
    for file in team_competition_season_values_files:
        db_handler.request_insert_or_update_many('team_competition_season',file,key_parameters=team_competition_season_key_parameters,parameters=team_competition_season_parameters)
    
    #insert teams competition season rounds
    for file in team_competition_season_round_values_files:
        db_handler.request_insert_or_update_many('team_competition_season_round',file,key_parameters=team_competition_season_round_key_parameters,parameters=team_competition_season_round_parameters)


def map_player_position(position:str,name:str):
    '''Maps player position and name to more generic values'''
    if position in ['cb','rcb','lcb','lcb3','rcb3']:
        position = 'cb'
        name = 'Centre Back'
    elif position in ['lb','lwb','lb5']:
        position = 'lb'
        name = 'Left Back'
    elif position in ['rb','rwb','rb5']:
        position = 'rb'
        name = 'Right Back'
    elif position in ['dmf','ldmf','rdmf']:
        position = 'dmf'
        name = 'Defensive Midfielder'
    elif position in ['lcmf','lcmf3','rcmf','rcmf3']:
        position = 'cmf'
        name = 'Central Midfielder'
    elif position in ['lamf','lwf','lw']:
        position = 'lw'
        name = 'Left Winger'
    elif position in ['ramf','rwf','rw']:
        position = 'rw'
        name = 'Right Winger'
    elif position in ['cf','ss']:
        position = 'cf'
        name = 'Striker'
    return position,name



def prepare_players_insert(players,season_id,player_advanced_stats:bool=False):
    '''Prepare players values for insert in db'''
    # prepare values files
    player_values_file_name = f'{tmp_folder}/players_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    player_values_file = open(player_values_file_name,'w',encoding='utf-8')
    player_positions_values_file_name = f'{tmp_folder}/player_positions_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    player_positions_values_file = open(player_positions_values_file_name,'w',encoding='utf-8')
    career_entry_values_file_name = f'{tmp_folder}/career_entry_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    career_entry_values_file = open(career_entry_values_file_name,'w',encoding='utf-8')

    for player in players:
        contractInfo = get_player_contract_info(player['wyId'])
        contractExpiration = ''
        player_agencies = ''
        if contractInfo:
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
        passportArea = process_mssql_value(player['passportArea']['id'])
        birthArea = process_mssql_value(player['birthArea']['id'])
        birthDate = process_date(player['birthDate'])
        birthDate = f'\'{birthDate}\'' if birthDate != 'NULL' else 'NULL'
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
        contractExpiration = f'\'{contractExpiration}\'' if contractExpiration != 'NULL' else 'NULL'
        player_agencies = process_mssql_value(player_agencies)
        current_team = process_mssql_number(player['currentTeamId'])
        market_value = 0
        currency = 'EUR'

        last_transfer = get_player_last_transfer(player['wyId'])
        if last_transfer:
            market_value = process_mssql_number(last_transfer["value"])
            currency = process_mssql_value(last_transfer["currency"])

        values = f'''('{wyId}', '{player_name}', '{shortName}','{passportArea}', '{birthArea}', \
                    {birthDate}, '{imageDataURL}', '{foot}',\
                    '{height}','{weight}','{status}','{gender}',\
                    '{role_code2}', '{role_code3}', '{role_name}','{market_value}',\
                    {contractExpiration},'{player_agencies}','{current_team}','{currency}')'''
        player_values_file.write(values)
        player_values_file.write(file_delimiter)


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

                values = f'''SELECT {wyId}, idteam_competition_season, {appearances},{goal},{minutesPlayed},\
                            {penalties},{redCards},{shirtNumber},{substituteIn},{substituteOnBench},\
                            {substituteOut},{yellowCard},{team},{season}
                            FROM "scouting"."team_competition_season" 
                            WHERE "team"={team} AND "competition_season"={season} '''
                career_entry_values_file.write(values)
                career_entry_values_file.write(file_delimiter)

                advanced_stats = get_player_advanced_stats(player['wyId'],competition,season)
                if advanced_stats:
                    # populate positions table
                    positions = advanced_stats['positions']
                    unique_positions = {}
                    # get unique positions in team season
                    for position in positions:
                        position_percent = process_mssql_value(position['percent'])
                        position_code = process_mssql_value(position['position']['code'])
                        position_name = process_mssql_value(position['position']['name'])
                        position_code,position_name = map_player_position(position_code,position_name)
                        if position_code not in unique_positions:
                            unique_positions[position_code] = {
                                'position_percent':position_percent,
                                'position_code':position_code,
                                'position_name':position_name
                            }
                        # if position already exists, sum position percent
                        else:
                            unique_positions[position_code]['position_percent'] += position_percent

                    for position in unique_positions.values():
                        values = f'''SELECT {wyId}, {position['position_percent']},'{position['position_code']}', '{position['position_name']}',idteam_competition_season \
                                    FROM "scouting"."team_competition_season" WHERE "team"={team} AND "competition_season"={season} '''
                        player_positions_values_file.write(values)
                        player_positions_values_file.write(file_delimiter)

        pbar_players.update(1)
    player_values_file.close()
    player_positions_values_file.close()
    career_entry_values_file.close()
    return [(player_values_file_name,'player'),(player_positions_values_file_name,'player_positions'),(career_entry_values_file_name,'career_entry')]
        
    

def populate_players(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates players table in db'''
    print(f'Populating players from season {season_id}')
    players = get_season_players(season_id)
    pbar_players.reset(total=len(players))
    result = run_threaded_for(prepare_players_insert,players,log=True,args=[season_id,player_advanced_stats],threads=12)
    values_files = [file for file_list in result for file in file_list]

    player_values_files = []
    player_positions_values_files = []
    career_entry_values_files = []
    # separate querys
    for file,type in values_files:
        if type == 'player':
            player_values_files.append(file)
        elif type == 'player_positions':
            player_positions_values_files.append(file)
        elif type == 'career_entry':
            career_entry_values_files.append(file)

    #insert players
    for file in player_values_files:
        db_handler.request_insert_or_update_many('player',file,key_parameters=player_key_parameters,parameters=player_parameters)

    #insert career entry
    for file in career_entry_values_files:
        db_handler.request_insert_or_update_many_union('career_entry',file,key_parameters=career_entry_key_parameters,parameters=career_entry_parameters)
    
    if player_advanced_stats:
        #insert player positions
        for file in player_positions_values_files:
            db_handler.request_insert_or_update_many_union('player_positions',file,key_parameters=player_positions_key_parameters,parameters=player_positions_parameters)


def prepare_match_players_stats_insert(match:int,get_players:bool=False):
    '''Prepare values for player_match_stats table in db'''
    querys = []
    players_list = []

    match_players_stats = get_match_players_stats(match,players=get_players)
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

        querys.append(values)
        if get_players:
            if player_stats['player']:
                players_list.append(player_stats['player'])
            # inconsistency (player is not registered in API), do not add this players stats
            else:
                querys.pop()
    if get_players:
        return querys,players_list
    return querys
    


def prepare_match_formation_insert(match:int,match_team_info:dict):
    '''Prepare values for match_formation table in db'''
    substitutes_querys = []
    formation_querys = []
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
                substitutes_querys.append(values)
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
                            '{shirt_number}', '{yellow_cards}', '{team_info['teamId']}', '{type}')'''
                formation_querys.append(values)
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
                    type = 'substitution'
                values = f'''('{match}', '{player_id}', '{assists}', '{goals}', '{own_goals}', '{red_cards}',\
                             '{shirt_number}', '{yellow_cards}', '{team_info['teamId']}', '{type}')'''
                formation_querys.append(values)

    return substitutes_querys,formation_querys



def match_goal_assist(goal_event,match_events):
    '''Check if goal event has assist
    
    Assist is a pass event that occurs with scorer as recipient and 
    was done within the same minute as the goal'''

    assist = None
    potential_passes = []
    for event in match_events:
        if event['pass'] != None:
            # pass is to the player and was done within the same minute as the goal
            if event['pass']['recipient'] == goal_event['player']['id'] and event['minute'] <= goal_event['minute'] and event['minute'] >= goal_event['minute'] -1:
                potential_passes.append(event)
    
    if potential_passes:
        # get pass with closest time to goal
        closest_pass = max(potential_passes, key=lambda x: x['minute']*60 + x['second'])
        assist = {
            'playerId':closest_pass['player']['id'],
            'minute':closest_pass['minute'],
            'second':closest_pass['second']
        }
    return assist


    



def prepare_matches_insert(matches,season_id,player_advanced_stats:bool=False):
    '''Prepare values for matches table in db'''

    # prepare values files
    matches_values_file_name = f'{tmp_folder}/matches_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    matches_values_file = open(matches_values_file_name,'w',encoding='utf-8')
    match_lineup_values_file_name = f'{tmp_folder}/match_lineup_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_lineup_values_file = open(match_lineup_values_file_name,'w',encoding='utf-8')
    match_lineup_player_position_values_file_name = f'{tmp_folder}/match_lineup_player_position_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_lineup_player_position_values_file = open(match_lineup_player_position_values_file_name,'w',encoding='utf-8')
    match_event_pass_values_file_name = f'{tmp_folder}/match_event_pass_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_event_pass_values_file = open(match_event_pass_values_file_name,'w',encoding='utf-8')
    match_event_shot_values_file_name = f'{tmp_folder}/match_event_shot_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_event_shot_values_file = open(match_event_shot_values_file_name,'w',encoding='utf-8')
    match_event_infraction_values_file_name = f'{tmp_folder}/match_event_infraction_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_event_infraction_values_file = open(match_event_infraction_values_file_name,'w',encoding='utf-8')
    match_event_carry_values_file_name = f'{tmp_folder}/match_event_carry_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_event_carry_values_file = open(match_event_carry_values_file_name,'w',encoding='utf-8')
    match_event_other_values_file_name = f'{tmp_folder}/match_event_other_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_event_other_values_file = open(match_event_other_values_file_name,'w',encoding='utf-8')
    match_substitution_values_file_name = f'{tmp_folder}/match_substitution_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_substitution_values_file = open(match_substitution_values_file_name,'w',encoding='utf-8')
    match_formation_values_file_name = f'{tmp_folder}/match_formation_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_formation_values_file = open(match_formation_values_file_name,'w',encoding='utf-8')
    match_player_stats_values_file_name = f'{tmp_folder}/match_player_stats_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_player_stats_values_file = open(match_player_stats_values_file_name,'w',encoding='utf-8')
    match_goals_values_file_name = f'{tmp_folder}/match_goals_{time.time()}_{random.randint(0,100000)}_{random.randint(0,100000)}.txt'
    match_goals_values_file = open(match_goals_values_file_name,'w',encoding='utf-8')

    # auxiliary values lists
    match_substitution_values = []
    match_formation_values = []
    match_player_stats_values = []
    matches_players_list = []

    for match in matches:
        match_info = get_match_info(match['matchId'])
        match_advanced_stats = get_match_advanced_stats(match['matchId'])
        if match_info:
            # get match basic info
            wyId = process_mssql_value(match_info['wyId'])
            seasonId = process_mssql_value(match_info['seasonId'])
            roundId = process_mssql_value(match_info['roundId'])
            home_team = process_mssql_value(match_info['teamsData']['home']['teamId'])
            home_score = process_mssql_value(match_info['teamsData']['home']['score'])
            away_team = process_mssql_value(match_info['teamsData']['away']['teamId'])
            away_score = process_mssql_value(match_info['teamsData']['away']['score'])
            dateutc = process_date_utc(match_info['dateutc'])
            dateutc = f'\'{dateutc}\'' if dateutc != 'NULL' else 'NULL'
            winner = process_mssql_value(match_info['winner'])
            duration = process_mssql_value(match_info['duration'])
            home_score_et = process_mssql_number(match_info['teamsData']['home']['scoreET'],default='0')
            home_score_ht = process_mssql_number(match_info['teamsData']['home']['scoreHT'],default='0')
            home_score_p = process_mssql_number(match_info['teamsData']['home']['scoreP'],default='0')
            away_score_et = process_mssql_number(match_info['teamsData']['away']['scoreET'],default='0')
            away_score_ht = process_mssql_number(match_info['teamsData']['away']['scoreHT'],default='0')
            away_score_p = process_mssql_number(match_info['teamsData']['away']['scoreP'],default='0')
            # match advanced stats
            home_shots = 0
            away_shots = 0
            home_shotsOnTarget = 0
            away_shotsOnTarget = 0
            home_xg = 0
            away_xg = 0
            home_attacks_total = 0
            away_attacks_total = 0
            home_corners = 0
            away_corners = 0
            home_possessionPercent = 0
            away_possessionPercent = 0
            home_fouls = 0
            away_fouls = 0
            home_pass_successful_percent = 0
            away_pass_successful_percent = 0
            home_vertical_pass_successful_percent = 0
            away_vertical_pass_successful_percent = 0
            home_offsides = 0
            away_offsides = 0
            home_clearances = 0
            away_clearances = 0
            home_interceptions = 0
            away_interceptions = 0
            home_tackles = 0
            away_tackles = 0
            if match_advanced_stats:
                home_shots                            = process_mssql_number(match_advanced_stats['general']['home']['shots'])
                away_shots                            = process_mssql_number(match_advanced_stats['general']['away']['shots'])
                home_shotsOnTarget                    = process_mssql_number(match_advanced_stats['general']['home']['shotsOnTarget'])
                away_shotsOnTarget                    = process_mssql_number(match_advanced_stats['general']['away']['shotsOnTarget'])
                home_xg                               = process_mssql_number(match_advanced_stats['general']['home']['xg'])
                away_xg                               = process_mssql_number(match_advanced_stats['general']['away']['xg'])
                home_attacks_total                    = process_mssql_number(match_advanced_stats['attacks']['home']['total'])
                away_attacks_total                    = process_mssql_number(match_advanced_stats['attacks']['away']['total'])
                home_corners                          = process_mssql_number(match_advanced_stats['general']['home']['corners'])
                away_corners                          = process_mssql_number(match_advanced_stats['general']['away']['corners'])
                home_possessionPercent                = process_mssql_number(match_advanced_stats['possession']['home']['possessionPercent'])
                away_possessionPercent                = process_mssql_number(match_advanced_stats['possession']['away']['possessionPercent'])
                home_fouls                            = process_mssql_number(match_advanced_stats['general']['home']['fouls'])
                away_fouls                            = process_mssql_number(match_advanced_stats['general']['away']['fouls'])
                home_pass_successful_percent          = process_mssql_number((match_advanced_stats['passes']['home']['passesSuccessful']*100)/match_advanced_stats['passes']['home']['passes'])
                away_pass_successful_percent          = process_mssql_number((match_advanced_stats['passes']['away']['passesSuccessful']*100)/match_advanced_stats['passes']['away']['passes'])
                home_vertical_pass_successful_percent = process_mssql_number((match_advanced_stats['passes']['home']['verticalPassesSuccessful']*100)/match_advanced_stats['passes']['home']['verticalPasses'])
                away_vertical_pass_successful_percent = process_mssql_number((match_advanced_stats['passes']['away']['verticalPassesSuccessful']*100)/match_advanced_stats['passes']['away']['verticalPasses'])
                home_offsides                         = process_mssql_number(match_advanced_stats['general']['home']['offsides'])
                away_offsides                         = process_mssql_number(match_advanced_stats['general']['away']['offsides'])
                home_clearances                       = process_mssql_number(match_advanced_stats['defence']['home']['clearances'])
                away_clearances                       = process_mssql_number(match_advanced_stats['defence']['away']['clearances'])
                home_interceptions                    = process_mssql_number(match_advanced_stats['defence']['home']['interceptions'])
                away_interceptions                    = process_mssql_number(match_advanced_stats['defence']['away']['interceptions'])
                home_tackles                          = process_mssql_number(match_advanced_stats['defence']['home']['tackles'])
                away_tackles                          = process_mssql_number(match_advanced_stats['defence']['away']['tackles'])



            values = f'''('{wyId}','{seasonId}','{roundId}', '{home_team}', '{away_team}', {dateutc},\
                    '{home_score}','{away_score}', '{winner}', '{duration}', '{home_score_et}', '{home_score_ht}',\
                    '{home_score_p}', '{away_score_et}', '{away_score_ht}', '{away_score_p}',\
                    '{home_shots}', '{away_shots}', '{home_shotsOnTarget}', '{away_shotsOnTarget}',\
                    '{home_xg}', '{away_xg}', '{home_attacks_total}', '{away_attacks_total}',\
                    '{home_corners}', '{away_corners}', '{home_possessionPercent}', '{away_possessionPercent}',\
                    '{home_fouls}', '{away_fouls}', '{home_pass_successful_percent}', '{away_pass_successful_percent}',\
                    '{home_vertical_pass_successful_percent}', '{away_vertical_pass_successful_percent}',\
                    '{home_offsides}', '{away_offsides}', '{home_clearances}', '{away_clearances}',\
                    '{home_interceptions}', '{away_interceptions}', '{home_tackles}', '{away_tackles}')'''

            matches_values_file.write(values)
            matches_values_file.write(file_delimiter)


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
            ms_values,mf_values = prepare_match_formation_insert(match['matchId'],match_info['teamsData'])
            match_substitution_values += ms_values
            match_formation_values += mf_values
            
            # get match lineups
            if match_lineups:
                teams = [x for x in match_lineups if x != "teams"]
                for team in teams:
                    lineup_info = match_lineups[team]
                    for part,times in lineup_info.items():
                        for second,lineups in times.items():
                            for lineup in lineups:
                                scheme = process_mssql_value(lineups[lineup]['scheme'])
                                values = f'''('{match['matchId']}', '{team}', '{part}', '{second}','{scheme}')'''
                                match_lineup_values_file.write(values)
                                match_lineup_values_file.write(file_delimiter)
                                players = lineups[lineup]['players']
                                # players positions in lineup
                                for playerdict in players:
                                    for playerId in playerdict:
                                        position = process_mssql_value(playerdict[playerId]['position'])
                                        values = f'''SELECT match_lineup_id, {playerId},'{position}' 
                                                    FROM "scouting"."match_lineup"
                                                    WHERE "match"='{match['matchId']}' AND "team"={team} AND "period"='{part}' AND "second"={second} '''
                                        match_lineup_player_position_values_file.write(values)
                                        match_lineup_player_position_values_file.write(file_delimiter)

            # get match advanced stats for each player
            if player_advanced_stats:
                query_list,players_list = prepare_match_players_stats_insert(match['matchId'],get_players=True)
                match_player_stats_values += query_list
                # get match players for populate (because of api inconsistency)
                matches_players_list += players_list
                

            # # get match events
            for event in match_events:
                id = process_mssql_value(event['id'])
                matchid = process_mssql_value(event['matchId'])
                player = process_mssql_value(event['player']['id'])
                matchPeriod = process_mssql_value(event['matchPeriod'])
                team = process_mssql_value(event['team']['id'])
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
                            , '{accurate}', '{recipient}', '{endlocation_x}', '{endlocation_y}', '{team}')'''
                    match_event_pass_values_file.write(values)
                    match_event_pass_values_file.write(file_delimiter)

                elif event['shot'] != None:
                    isGoal = process_mssql_bool(event['shot']['isGoal'])
                    onTarget = process_mssql_bool(event['shot']['onTarget'])
                    xg = process_mssql_number(event['shot']['xg'])
                    postShotXg = process_mssql_number(event['shot']['postShotXg'])
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}'
                            , '{isGoal}', '{onTarget}', '{xg}', '{postShotXg}', '{team}')'''
                    match_event_shot_values_file.write(values)
                    match_event_shot_values_file.write(file_delimiter)
                    # if goal add to match_goals
                    if isGoal == '1':
                        assist = match_goal_assist(event,match_events)
                        assistant = 'null'
                        assist_minute = 'null'
                        assist_second = 'null'
                        if assist:
                            assistant = f"'{process_mssql_value(assist['player'])}'"
                            assist_minute = f"'{process_mssql_number(assist['minute'])}'"
                            assist_second = f"'{process_mssql_number(assist['second'])}'"
                        values = f'''('{id}', '{matchid}', '{player}', '{minute}', '{second}', {assistant}, {assist_minute}, {assist_second},\
                                '{team}')'''
                        match_goals_values_file.write(values)
                        match_goals_values_file.write(file_delimiter)

                elif event['infraction'] != None and (event['infraction']['yellowCard'] or event['infraction']['redCard']):
                    yellowCard = process_mssql_bool(event['infraction']['yellowCard'])
                    redCard = process_mssql_bool(event['infraction']['redCard'])
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}'
                            , '{yellowCard}', '{redCard}', '{team}')'''
                    match_event_infraction_values_file.write(values)
                    match_event_infraction_values_file.write(file_delimiter)

                elif event['carry'] != None:    
                    endlocation_x = process_mssql_number(event['carry']['endLocation']['x'])
                    endlocation_y = process_mssql_number(event['carry']['endLocation']['y'])
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}'
                            , '{endlocation_x}', '{endlocation_y}', '{team}')'''
                    match_event_carry_values_file.write(values)
                    match_event_carry_values_file.write(file_delimiter)

                else:
                    values = f'''('{id}', '{matchid}', '{player}', '{matchPeriod}', '{location_x}', '{location_y}', '{minute}', '{second}',\
                            '{team}')'''
                    match_event_other_values_file.write(values)
                    match_event_other_values_file.write(file_delimiter)
        pbar_matches.update(1)

    matches_values_file.close()
    match_lineup_values_file.close()
    match_lineup_player_position_values_file.close()
    match_event_pass_values_file.close()
    match_event_shot_values_file.close()
    match_event_infraction_values_file.close()
    match_event_carry_values_file.close()
    match_event_other_values_file.close()


    for value in match_substitution_values:
        match_substitution_values_file.write(value)
        match_substitution_values_file.write(file_delimiter)
    match_substitution_values_file.close()

    for value in match_formation_values:
        match_formation_values_file.write(value)
        match_formation_values_file.write(file_delimiter)
    match_formation_values_file.close()

    for value in match_player_stats_values:
        match_player_stats_values_file.write(value)
        match_player_stats_values_file.write(file_delimiter)
    match_player_stats_values_file.close()

    # prepare insert of non existent players
    matches_players_list = db_non_existent_players(matches_players_list)
    results = prepare_players_insert(matches_players_list,season_id,player_advanced_stats=player_advanced_stats)
    player_values_file_name = results[0][0]
    player_positions_values_file_name = results[1][0]
    career_entry_values_file_name = results[2][0]


    return [(matches_values_file_name,'match'),(player_values_file_name,'player'),(player_positions_values_file_name,'player_positions'),
            (career_entry_values_file_name,'career_entry'),(match_lineup_values_file_name,'match_lineup'),
            (match_lineup_player_position_values_file_name,'match_lineup_player_position'),(match_event_pass_values_file_name,'match_event_pass'),
            (match_event_shot_values_file_name,'match_event_shot'),(match_event_infraction_values_file_name,'match_event_infraction'),
            (match_event_carry_values_file_name,'match_event_carry'),(match_event_other_values_file_name,'match_event_other'),
            (match_substitution_values_file_name,'match_substitution'),(match_formation_values_file_name,'match_formation'),
            (match_player_stats_values_file_name,'player_match_stats'),(match_goals_values_file_name,'match_goals')]
        



def populate_matches(db_handler:Db_handler,season_id:int,player_advanced_stats:bool=False):
    '''Populates matches table in db, gathering matches from given season\n
    Can gather advanced stats from players in each match'''
    print(f'Populating matches from season {season_id}')
    matches = get_season_matches(season_id)
    pbar_matches.reset(total=len(matches))
    pbar_players.disable = True
    result = run_threaded_for(prepare_matches_insert,matches,log=True,args=[season_id,player_advanced_stats],threads=10)
    pbar_players.disable = False
    pbar_matches.refresh()
    pbar_matches.reset()
    pbar_players.clear()
    values_files = [file for files_list in result for file in files_list]
    match_values_files = []
    player_values_files = []
    career_entry_values_files = []
    player_positions_values_files = []
    player_match_stats_values_files = []
    match_lineup_values_files = []
    match_lineup_player_position_values_files = []
    match_formation_values_files = []
    match_substitution_values_files = []
    match_goals_values_files = []
    match_events_values_files = {
        "pass" : [],
        "shot" : [],
        "infraction" : [],
        "carry" : [],
        "other" : []
    }
    # separate querys
    for file,type in values_files:
        if type == 'match':
            match_values_files.append(file)
        elif type == 'player':
            player_values_files.append(file)
        elif type == 'player_match_stats':
            player_match_stats_values_files.append(file)
        elif type == 'career_entry':
            career_entry_values_files.append(file)
        elif type == 'player_positions':
            player_positions_values_files.append(file)
        elif type == 'match_lineup':
            match_lineup_values_files.append(file)
        elif type == 'match_lineup_player_position':
            match_lineup_player_position_values_files.append(file)
        elif type == 'match_formation':
            match_formation_values_files.append(file)
        elif type == 'match_substitution':
            match_substitution_values_files.append(file)
        elif type == 'match_event_pass':
            match_events_values_files['pass'].append(file)
        elif type == 'match_event_shot':
            match_events_values_files['shot'].append(file)
        elif type == 'match_event_infraction':
            match_events_values_files['infraction'].append(file)
        elif type == 'match_event_carry':
            match_events_values_files['carry'].append(file)
        elif type == 'match_event_other':
            match_events_values_files['other'].append(file)
        elif type == 'match_goals':
            match_goals_values_files.append(file)

    # # match table
    for file in match_values_files:
        db_handler.request_insert_or_update_many('match',file,key_parameters=match_key_parameters,parameters=match_parameters)

    # player table
    for file in player_values_files:
        db_handler.request_insert_or_update_many('player',file,key_parameters=player_key_parameters,parameters=player_parameters)

    # career_entry table
    for file in career_entry_values_files:
        db_handler.request_insert_or_update_many_union('career_entry',file,key_parameters=career_entry_key_parameters,parameters=career_entry_parameters)

    # player_positions table
    for file in player_positions_values_files:
        db_handler.request_insert_or_update_many_union('player_positions',file,key_parameters=player_positions_key_parameters,parameters=player_positions_parameters)
                         

    if player_advanced_stats:
        # player_match_stats table
        for file in player_match_stats_values_files:
            db_handler.request_insert_or_update_many('player_match_stats',file,key_parameters=player_match_stats_key_parameters,parameters=player_match_stats_parameters)

    # match_lineup table
    for file in match_lineup_values_files:
        db_handler.request_insert_or_update_many('match_lineup',file,key_parameters=match_lineup_key_parameters,parameters=match_lineup_parameters)

    # match_lineup_player_position table
    for file in match_lineup_player_position_values_files:
        db_handler.request_insert_or_update_many_union('match_lineup_player_position',file,key_parameters=match_lineup_player_position_key_parameters,
                                     parameters=match_lineup_player_position_parameters)

    # match_formation table
    for file in match_formation_values_files:
        db_handler.request_insert_or_update_many('match_formation',file,key_parameters=match_formation_key_parameters,parameters=match_formation_parameters)

    # match_substitution table
    for file in match_substitution_values_files:
        db_handler.request_insert_or_update_many('match_substitution',file,key_parameters=match_substitution_key_parameters,parameters=match_substitution_parameters,batch_size=3000)

    # match_event table
    # other
    for file in match_events_values_files['other']:
        db_handler.request_insert_or_update_many('match_event_other',file,key_parameters=match_event_other_key_parameters,parameters=match_event_other_parameters,batch_size=3000)

    # pass
    for file in match_events_values_files['pass']:
        db_handler.request_insert_or_update_many('match_event_pass',file,key_parameters=match_event_pass_key_parameters,parameters=match_event_pass_parameters,batch_size=3000)

    # shot
    for file in match_events_values_files['shot']:
        db_handler.request_insert_or_update_many('match_event_shot',file,key_parameters=match_event_shot_key_parameters,parameters=match_event_shot_parameters,batch_size=3000)

    # goals
    for file in match_goals_values_files:
        db_handler.request_insert_or_update_many('match_goals',file,key_parameters=match_goals_key_parameters,parameters=match_goals_parameters,batch_size=3000)

    # carry
    for file in match_events_values_files['carry']:
        db_handler.request_insert_or_update_many('match_event_carry',file,key_parameters=match_event_carry_key_parameters,parameters=match_event_carry_parameters,batch_size=3000)

    # infraction
    for file in match_events_values_files['infraction']:
        db_handler.request_insert_or_update_many('match_event_infraction',file,key_parameters=match_event_infraction_key_parameters,parameters=match_event_infraction_parameters,batch_size=3000)
    

def get_full_info(db_handler:Db_handler):
    request_file_path = f'{current_folder}/{args.full_info[0]}'
    if request_file_path.endswith('json') and os.path.exists(request_file_path):
        request_file = json.load(open(request_file_path))
        # populate areas
        populate_areas(db_handler) 
        if 'competitions' in request_file:
            competitions = request_file['competitions']
            competitions_info = extract_competitions_info(competitions)
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


def main(args,db_handler:Db_handler):
    '''Main function'''

    #TODO : treat other optional flags

    # get full info
    if args.full_info:
        get_full_info(db_handler)
        




if __name__ == '__main__':
    args = parse_arguments()

    if args.db_config[0].endswith('.json'):
        tmp_folder = f'{current_folder}/tmp'
        file_delimiter = '|;|'
        # data insert tmp folder
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)
        # clean folder
        else:
            for file in os.listdir(tmp_folder):
                os.remove(f'{tmp_folder}/{file}')

        db_config_path = f'{current_folder}/{args.db_config[0]}'
        db_logger = None
        main_logger = None
        if args.log:
            logging.basicConfig(level=logging.INFO)
            db_logger = logging.getLogger('db_logger')
            main_logger = logging.getLogger('main_logger')
            main_logger.log(logging.INFO,'Logging active')

        # db request handler - for requests that are not time sensitive (can be done when available)
        db_request_handler = Db_handler(config_json=db_config_path,logger=db_logger)
        db_request_handler.create_connection()
        # db connection - for requests that are time sensitive (must be done as soon as possible)
        db_connection = Db_handler(config_json=db_config_path,logger=db_logger)
        db_connection.create_connection()

        if db_connection.connection and db_request_handler.connection:
            try:
                # db_handler run request handler loop
                request_handler_thread = threading.Thread(target=db_request_handler.run_request_handler,daemon=True)
                request_handler_thread.start()

                start_time = time.time()
                # main function - get api data
                main(args,db_request_handler)
                end_request_time = time.time()
                print(f'API requests finished in {end_request_time-start_time} seconds.')

                # close db connection
                db_connection.close_connection()
                db_request_handler.request_close_connection()
                print('Waiting for db handler thread to finish...')
                request_handler_thread.join()
                end_time = time.time()
                print('DB handler thread finished.')
                print(f'Program finished in {end_time-start_time} seconds.')
                print(f'API requests finished in {end_request_time-start_time} seconds.')
                print(f'DB requests finished in {end_time-end_request_time} seconds.')
            except Exception as e:
                print(e)
                db_connection.close_connection()
                db_request_handler.close_connection()
                print('Waiting for db handler thread to finish...')
                request_handler_thread.join(timeout=1)
                print('DB handler thread finished.')
        else:
            print('DB connection failed to be established.')
    else:
        print('Invalid db config file. Please provide a .json file.')



                        