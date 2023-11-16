import requests
from bs4 import BeautifulSoup
import json
import argparse
import os
import re
from db import Db_handler
import logging
from utils import similarity
from datetime import date
import time
from requests.exceptions import ChunkedEncodingError
import sys


max_retries = 30
chunked_error_time_sleep = 3
other_error_time_sleep = 60

def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--db_config','-dbc'            ,type=str, nargs=1,required=True                                , help='Db config json file path')
    parser.add_argument('--complete_name','-cn'         ,action='store_true'                                            , help='Request complete name of player' )
    return parser.parse_args()

today = date.today()

headers = {'User-Agent': 
               'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36'}

t = "''-ĀāĂăĄąÀàÁáÂâÃãÄäÅåÆæÞþßÇçĆćĈĉĊċČčÐĎďĐđÈèÉéÊêËëĒēĔĕĖėĘęĚěðĜĝĞğĠġĢģĤĥĦħÌìÍíÎîÏïĨĩĪīĬĭĮįİıĴĵĶķĸĹĺĻļĽľĿŀŁłÑñŃńŅņŇňŉŊŋØÒòÓóÔôÕõÖöŌōŎŏŐőøŔŕŖŗŘřŚśŜŝŞşŠšŢţŤťŦŧÙùÚúÛûÜüŨũŪūŬŭŮůŰűŲųŴŵÝýŶŷŸÿŹźŻżŽž×"
tt = "  AaAaAaAaAaAaAaAaAaAabbBCcCcCcCcCcDDdDdEeEeEeEeEeEeEeEeEeeGgGgGgGgHhHhIiIiIiIiIiIiIiIiIiJjKkkLlLlLlLlLlNnNnNnNnnNnOOoOoOoOoOoOoOoOooRrRrRrSsSsSsSsTtTtTtUuUuUuUuUuUuUuUuUuUuWwYyYyYyZzZzZzx"

def get_age(birth_date):
    return int(today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day)))

def treat_market_value(market_value : str):
    value = 0
    if market_value != '' and market_value != '-':
        value = float(market_value[1:-1])
    if 'm' in market_value or 'M' in market_value:
        value *= 1000000
    elif 'k' in market_value or 'K' in market_value:
        value *= 1000

    return int(value)

def translate(name):
    return f"translate({name} , '{t}', '{tt}')"

def sq(name):
    return f"'{name}'"

def like(where, like):
    return f'{translate(where)} like {translate(sq(like))}'

def like_multiple(where, likes):
    result = ""
    like_str = f'{translate(where)} like'
    #like_str = f'{where} like'
    if len(likes) > 0:
        result = f'{like_str} {translate(sq(likes[0]))}' 
        for like in likes[1:]:
            result += f' or {like_str} {translate(sq(like))}'
        return result
    else:
        return result

def extract_tm_id(url):
    # Use uma expressão regular para encontrar o ID no URL
    match = re.search(r'/verein/(\d+)/saison_id/(\d+)', url)
    
    if match:
        # Retorna o valor correspondente ao grupo 1 (o ID) da expressão regular
        return int(match.group(1)),int(match.group(2))
    else:
        # Se não encontrar um ID, você pode retornar um valor padrão ou levantar uma exceção, conforme necessário
        return None
    
def extract_p_tm_id(url):
    match = re.search(r'/profil/spieler/(\d+)',url)
    if match:
        # Retorna o valor correspondente ao grupo 1 (o ID) da expressão regular
        return int(match.group(1))
    else:
        # Se não encontrar um ID, você pode retornar um valor padrão ou levantar uma exceção, conforme necessário
        return None
    
def safe_request(url, headers):
    retries = 0
    while retries < max_retries:
        try:
            return requests.get(url, headers=headers)
        except ChunkedEncodingError as e:
            print(f"Caught ChunkedEncodingError. Retrying ({retries + 1}/{max_retries})... sleeping {chunked_error_time_sleep}")
            time.sleep(chunked_error_time_sleep)  # Add a delay before retrying
            retries += 1
        except e:
            print(f"Caught {e}. Retrying ({retries + 1}/{max_retries})... sleeping {other_error_time_sleep}")
            time.sleep(other_error_time_sleep)  # Add a delay before retrying
            retries += 1
        
def scrap_player_name(tm_id):
    url = f"https://www.transfermarkt.pt/player/profil/spieler/{tm_id}"
    pageTree = requests.get(url, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

    table = pageSoup.find("div", {"class" : "info-table info-table--right-space"})
    complete_name = table.find("span",{"class" : "info-table__content info-table__content--bold"}).text if table else ""
    return complete_name

def scrap_official_name(tm_id):
    url = f"https://www.transfermarkt.com/club/datenfakten/verein/{tm_id}"
    pageTree = requests.get(url, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')

    div_content = pageSoup.find("div", {"class" : "content"})
    profileheader = div_content.find("table",{"class" : "profilheader"})
    tr = profileheader.find("tr")
    td = tr.find("td")
    official_name = td.text
    return official_name

def scrap_players(tm_id,season):
    players = {}
    url = f"https://www.transfermarkt.com/club/kader/verein/{tm_id}/saison_id/{season}"
    pageTree = requests.get(url, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')
    #Scrapping all team names
    table = pageSoup.find("table", {"class" : "items"})
    tbody = table.find("tbody")
    trs_odd = tbody.find_all("tr", {"class" : "odd"})
    trs_even = tbody.find_all("tr", {"class" : "even"})
    for tr in trs_odd + trs_even:
        number = tr.find("div",{"class" : "rn_nummer"}).text
        table_inline = tr.find("table",{"class":"inline-table"})
        td_name = table_inline.find("td",{"class":"hauptlink"})
        name = td_name.text.strip()
        p_tm_id = extract_p_tm_id(td_name.find("a")['href'])
        marketvalue = tr.find("td",{"class" : "rechts hauptlink"}).text.strip()
        
        tds = tr.find_all("td",{"class" : "zentriert"})[1:3]
        age = tds[0].text
        nat = tds[1].find("img")['title']
        players[name] = {
            "number" :number,
            "market_value" : treat_market_value(marketvalue),
            "age" : age,
            "nat" : nat,
            "tm_id" : p_tm_id,
        }
    return players

def scrap_comp_info(comp_code):
    if comp_code == None or comp_code == 'None':
        return None
    print(f"Scrapping competition: {comp_code}")
    comp = {}
    url = f"https://www.transfermarkt.com/comp/startseite/wettbewerb/{comp_code}"
    pageTree = requests.get(url, headers=headers)
    pageSoup = BeautifulSoup(pageTree.content, 'html.parser')
    
    #Scrapping all team names
    table = pageSoup.find("table", {"class" : "items"})
    tbody = table.find("tbody")
    trs = tbody.find_all("tr")
    for tr in trs:
        td = tr.find("td", {"class" : "hauptlink no-border-links"})
        team_name = td.text
        a = td.find("a")
        tm_id,season = extract_tm_id(a['href'])
        official_name = scrap_official_name(tm_id)
        print(f"Scrapping team: {official_name}")
        players = scrap_players(tm_id,season)
        comp[team_name] = {
            "players" : players,
            "tm_id" : tm_id,
            "official_name" : official_name
        }


    return comp

def test_similarity(bd_team_name,bd_team_official_name,tm_team_name,tm_team_official_name):
    s1 = similarity(tm_team_name,bd_team_name)
    s2 = similarity(tm_team_official_name,bd_team_name)
    s3 = similarity(tm_team_name, bd_team_official_name)
    s4 = similarity(tm_team_official_name,bd_team_official_name)
    return max(max(s1,s2),max(s3,s4))

def treat_name(name):
    name = name.replace("'","")
    return name.replace("-"," ")

def find_player_by_complete_name(p_tm_id : int, current_team:int):
    player_complete_name = scrap_player_name(p_tm_id)
    player_complete_name = player_complete_name.replace(" ","%")
    player_complete_name = player_complete_name.replace("'","")
    select_players3 = db_handler.select("player","idplayer,birth_date,name",f"where {like('name',f'%{player_complete_name}%')} and current_team={current_team}", log=True)
    players_selected = select_players3 if select_players3 else []
    return players_selected

def find_player_by_name(player_name : str, current_team : int):
    #Se nao encontrou então procurar pelo nome completo
    player_name = treat_name(player_name)
    player_names = player_name.split(" ")
    if(len(player_names) == 1):
        select_players2 = db_handler.select("player","idplayer,birth_date,name",f"where ({like_multiple('name',[f'%{player_name}%',f'{player_name}%',f'%{player_name}'])}) and current_team={current_team}")
        players_selected = select_players2 if select_players2 else []
    else:
        comparation = f"%{player_names[0]}"
        for n in player_names[1:]:
            comparation+= f"%{n}"
        comparation += "%"
        select_players2 = db_handler.select("player","idplayer,birth_date,name",f"where {like('name',f'{comparation}')} and current_team={current_team}", log=False)
        players_selected = select_players2 if select_players2 else []
    return players_selected

def find_player_by_short_name(player_name : str, current_team : int):
    player_name = treat_name(player_name)
    player_names = player_name.split(" ")
    if (len(player_names) == 1):
        select_players = db_handler.select("player",'idplayer,birth_date,short_name',f"where ({like('short_name',f'%{player_name}%')}) and current_team={current_team}", log=False)
        players_selected = select_players if select_players else []
    elif (len(player_names) == 2):
        player_name = f"{player_names[0]}%{player_names[1]}"
        player_name2 = f"{player_names[0][0]}.%{player_names[1]}"
        player_name3 = f"{player_names[1][0]}.%{player_names[0]}"
        player_name4 = f"{player_names[1]}%{player_names[0]}"
        select_players = db_handler.select("player",'idplayer,birth_date,short_name',f"where ({like_multiple('short_name',[f'%{player_name}%',f'%{player_name2}%',f'%{player_name3}%',f'%{player_name4}%'])}) and current_team={current_team}", log=False)
        players_selected = select_players if select_players else []
    else:
        player_name2 = f"{player_names[0][0]}."
        for n in player_names[1:]:
            player_name2 += f" {n}"
        select_players = db_handler.select("player",'idplayer,birth_date,short_name',f"where ({like_multiple('short_name',[f'%{player_name}%',f'%{player_name2}%'])}) and current_team={current_team}", log=False)
        players_selected = select_players if select_players else []
    return players_selected

def test_players_selected(players_selected : list, assigned_players : list, player_age : int):
    for player_select in players_selected:
        id,birth_date,name = player_select
        if id in assigned_players or player_age != get_age(birth_date):
            players_selected.remove(player_select)

def db_update_tmvalue(player_market_value, player_id):
    db_handler.update("player", ["tm_market_value","tm_market_value_currency","tm_scrap"], [player_market_value,"'EUR'","'1'"], f"WHERE idplayer = {player_id}", log=False)

def update_market_value(players_selected : list, assigned_players : list, player_market_value : int, player_name : str):
    if(len(players_selected) == 1):
        #Dar update do valor de mercado
        assigned_players.append(players_selected[0][0])
        db_update_tmvalue(player_market_value,players_selected[0][0])
        print(f"{player_name} updated!")
        return True
    elif(len(players_selected) > 0):
        #Comparar e ver qual deles é o real
        max_similarity = 0
        actual_id = None
        found = False
        for id,_,short_name in players_selected:
            actual_similarity = similarity(short_name,player_name)
            if actual_similarity == 1:
                found = True
                #Dar update do valor de mercado
                assigned_players.append(id)
                db_update_tmvalue(player_market_value,id)
                print(f"{player_name} updated!")
                break
            elif actual_similarity > max_similarity:
                actual_id = id
        if not found:
            #Escolher o com maior similiradidade de short name
            #Dar update do valor de mercado
            assigned_players.append(actual_id)
            db_update_tmvalue(player_market_value,actual_id)
            print(f"{player_name} updated!")
        return True
    else:
        return False

def main(db_handler, cn : bool):
    start_time = time.time()
    #geting tm code of all competitions in bd
    comp_codes = db_handler.select("competition","idcompetitions,custom_name", log=False)
    #comp_codes = [(255, 'BRA1'),(146, 'CDLP')]
    not_found_players_file = open("nfp.txt","w+")

    for (comp_id,comp_code) in comp_codes:
        comp_info = scrap_comp_info(comp_code)
        #comp_info = json.load(open(f"test_{comp_code}.json"))
        if comp_info == None:
            continue
        
        #Serializing json   
        #json_object = json.dumps(comp_info, indent = 4)  
        #f = open(f"test_{comp_code}.json", "w")
        #f.write(json_object)
        #f.close()
       
        select_competitions_seasons = db_handler.select("competition_season","idcompetition_season", f'where "competition" = {comp_id} order by "competition_season"."startDate" desc limit 1',log=False)
        competition_season = select_competitions_seasons[0][0] if select_competitions_seasons else None


        if competition_season:
            select_teams_ids = db_handler.select("team_competition_season","team",f"where competition_season = {competition_season}", log=False)
            teams_ids = {id_team:{} for (id_team,) in select_teams_ids} if select_teams_ids else {}
            queue = list(teams_ids.keys())
            for team_id in queue:
                select_team_names = db_handler.select("team","name,official_name",f"where idteam = {team_id}", log=False)
                bd_team_names = select_team_names[0] if select_team_names else None
                if bd_team_names:
                    bd_team_name, bd_team_official_name = bd_team_names
                    teams_ids[team_id]['bd_team_name'] = bd_team_name
                    teams_ids[team_id]['bd_team_official_name'] = bd_team_official_name
            
            next_queue = list(queue)
            for team_id in next_queue:
                for tm_team_name,tm_team_info in comp_info.items():
                    if('id' in tm_team_info):
                        continue
                    bd_team_name = teams_ids[team_id]['bd_team_name']
                    bd_team_official_name = teams_ids[team_id]['bd_team_official_name']
                    tm_team_official_name = tm_team_info['official_name']
                    actual_similarity = test_similarity(bd_team_name,bd_team_official_name,tm_team_name,tm_team_official_name)
                    if actual_similarity == 1:
                        tm_team_info["id"] = team_id
                        tm_team_info["bd_name"] = bd_team_name
                        queue.remove(team_id)
                        break

            
            matches = True
            while matches:
                matches = False
                next_queue = list(queue)
                for team_id in next_queue:
                    most_similarity = 0
                    actual_match = None
                    bd_team_name = teams_ids[team_id]['bd_team_name']
                    bd_team_official_name = teams_ids[team_id]['bd_team_official_name']
                    name_split = bd_team_name.split(" ")
                    name_split2 = bd_team_official_name.split(" ")
                    match_names = set([name for name in name_split + name_split2 if len(name) > 2])
                    possible_match_teams = list()
                    for tm_team_name,tm_team_info in comp_info.items():
                        if('id' in tm_team_info and 'most_similarity' not in tm_team_info):
                            continue
                        tm_team_official_name = tm_team_info['official_name']
                        for match_name in match_names:
                            if match_name in tm_team_name or match_name in tm_team_official_name:
                                possible_match_teams.append(tm_team_name)
                                break

                    for tm_team_name in possible_match_teams:
                        actual_similarity = test_similarity(bd_team_name,bd_team_official_name,tm_team_name,tm_team_official_name)
                        if actual_similarity > most_similarity and ('most_similarity' not in comp_info[tm_team_name] or comp_info[tm_team_name]['most_similarity'] < actual_similarity):
                            actual_match = tm_team_name
                            most_similarity = actual_similarity

                    if actual_match is not None:
                        if 'most_similarity' not in comp_info[actual_match]:
                            comp_info[actual_match]['most_similarity'] = most_similarity
                            comp_info[actual_match]['id'] = team_id
                            comp_info[actual_match]["bd_name"] = bd_team_name
                            queue.remove(team_id)
                            matches = True
                        elif comp_info[actual_match]['most_similarity'] < most_similarity:
                            queue.append(comp_info[actual_match]['id'])
                            comp_info[actual_match]['most_similarity'] = most_similarity
                            comp_info[actual_match]['id'] = team_id
                            comp_info[actual_match]["bd_name"] = bd_team_name
                            matches = True
                

            next_queue = list(queue)
            for team_id in next_queue:
                most_similarity = 0
                actual_match = None
                bd_team_name = teams_ids[team_id]['bd_team_name']
                bd_team_official_name = teams_ids[team_id]['bd_team_official_name']
                for tm_team_name,tm_team_info in comp_info.items():
                    if('id' in tm_team_info):
                        continue
                    tm_team_official_name = tm_team_info['official_name']
                    actual_similarity = test_similarity(bd_team_name,bd_team_official_name,tm_team_name,tm_team_official_name)
                    if actual_similarity > most_similarity:
                        actual_match = tm_team_name
                        most_similarity = actual_similarity
                
                if actual_match is not None:
                    comp_info[actual_match]['id'] = team_id
                    comp_info[actual_match]["bd_name"] = bd_team_name

            for tm_team_name,tm_team_info in comp_info.items():
                players = tm_team_info['players']
                if('id' not in tm_team_info):
                    continue
                current_team = tm_team_info['id']
                assigned_players = []
                for player_name,player_info in players.items():
                    player_name = treat_name(player_name)
                    player_age = int(player_info['age'])
                    player_market_value = player_info['market_value']
                    #try to find player by short_name
                    players_selected = find_player_by_short_name(player_name,current_team)
                    test_players_selected(players_selected, assigned_players, player_age)
                    if not update_market_value(players_selected, assigned_players, player_market_value, player_name):
                        #Se nao encontrou então procurar pelo nome completo
                        players_selected = find_player_by_name(player_name,current_team)
                        test_players_selected(players_selected, assigned_players, player_age)
                        if not update_market_value(players_selected, assigned_players, player_market_value, player_name):
                            if cn:
                                players_selected = find_player_by_complete_name(player_info['tm_id'],current_team)
                                if not update_market_value(players_selected, assigned_players, player_market_value, player_name):
                                    not_found_players_file.write(f"{player_name} not found with club {tm_team_name}\n")
                            else:
                                not_found_players_file.write(f"{player_name} not found with club {tm_team_name}\n")
    print(f'Finished in {time.time()-start_time} seconds')

if __name__ == '__main__':
    args = parse_arguments()
    if args.db_config[0].endswith('.json'):
        current_folder = os.path.dirname(__file__)
        db_config_path = f'{current_folder}/{args.db_config[0]}'
        logging.basicConfig(level=logging.INFO)
        db_logger = logging.getLogger('db_logger')
        db_handler = Db_handler(config_json=db_config_path,logger=db_logger)
        db_handler.create_connection()
        if db_handler.connection:
            main(db_handler,args.complete_name)
            db_handler.close_connection()
        else:
            print('DB connection failed to be established.')
    else:
        print('Invalid db config file. Please provide a .json file.')