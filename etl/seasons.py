#!/usr/bin/python3
import curses
from curses import panel
import os
import json
from utils import get_similar
from api_handler import get_area_competitions,get_competition_info,get_seasons_info_competitions,get_season_info
import argparse


current_folder = os.path.dirname(os.path.abspath(__file__))
competitions_requests_folder = f'{current_folder}/competitions'
if os.path.isdir(competitions_requests_folder):
    requests_files = os.listdir(competitions_requests_folder)

def parse_arguments():
    '''Define and parse arguments using argparse'''
    parser = argparse.ArgumentParser(description='wyscout API request')
    parser.add_argument('--request_file','-rf'            ,type=str, nargs=1      , help="Ficheiro request input")
    parser.add_argument('--list','-list'                  ,action='store_true'    , help="Lista informação")
    parser.add_argument('--add','-add'                    ,action='store_true'    , help="Adiciona informação")
    parser.add_argument('--remove','-rem'                 ,action='store_true'    , help="Remove informação")
    parser.add_argument('--comp','-comp'                  ,type=str, nargs=1      , help="Competição por nome")
    parser.add_argument('--comp_id','-comp_id'            ,type=str, nargs=1      , help="Competição por id")
    parser.add_argument('--season','-season'              ,type=str, nargs=1      , help="Season por nome/data")
    parser.add_argument('--season_id','-season_id'        ,type=str, nargs=1      , help="Season por id")
    parser.add_argument('--custom_name', '-custom_name'   ,type=str, nargs=1      , help="Custom name da competição")
    parser.add_argument('--area', '-area'   ,type=str, nargs=1                    , help="Area da competição")
    return parser.parse_args()


def my_raw_input(stdscr, r, c, prompt_string):
    curses.echo() 
    stdscr.addstr(r, c, prompt_string)
    stdscr.refresh()
    input = stdscr.getstr(r + 1, c, 20)
    return input

def verifica_temporada(comp_id,season):
    if 'wyId' in season:
        season['wyId'] = int(season['wyId'])
        wyId = season['wyId']
        result = get_season_info(wyId)
        if result and 'name' in result:
            season['name'] = result['name']
            season['start'] = result['startDate']
            season['end'] = result['endDate']
            return True
        else:
            return False
    else:
        name = season['name']
        seasons = get_seasons_info_competitions(comp_id)
        seasons_names = [s['season']['name'] for s in seasons['seasons']]
        if len(seasons_names) > 0:
            true_season_name = get_similar(seasons_names,name)
            season['wyId'],season['start'],season['end'] = [(s['seasonId'],s['season']['startDate'],s['season']['endDate']) for s in seasons['seasons'] if s['season']['name'] == true_season_name][0]
            season['name'] = true_season_name
            season['wyId'] = int(season['wyId'])
            return True
        else:
            return False

def verifica_competicao(comepetition):
    if 'wyId' in comepetition:
        wyId = comepetition['wyId']
        result = get_competition_info(wyId)
        if result and 'name' in result:
            comepetition['name'] = result['name']
            comepetition['area'] = result['area']['alpha3code']
            return True
        else:
            return False
    else:
        name = comepetition['name']
        area = comepetition['area']
        area_competitions = get_area_competitions(area=area)
        competitions_names = [c['name'] for c in area_competitions]
        if len(competitions_names) > 0:
            true_competition_name = get_similar(competitions_names,name)
            comepetition['wyId'] = [c['wyId'] for c in area_competitions if c['name'] == true_competition_name][0]
            comepetition['name'] = true_competition_name
            return True
        else:
            return False


def add_competicao(data,competition):
    data['competitions'].append(competition)

def add_temporada(data, season, comp_name = None, comp_id = None):
    if comp_name is None and comp_id is None:
        return
    for competicao in data["competitions"]:
        if competicao["name"] == comp_name or competicao['wyId'] == comp_id:
            competicao['seasons'].append(season)
            break

def remover_competicao(data, comp_name = None, comp_id = None):
    removed = False
    if comp_name is None and comp_id is None:
        return removed
    for competicao in data["competitions"]:
        if competicao["name"] == comp_name or competicao['wyId'] == comp_id:
            data["competitions"].remove(competicao)
            removed = True
            break
    return removed

def remover_temporada(data, comp_name = None,comp_id = None,season_name = None, season_id = None):
    removed = False
    if (comp_name is None and comp_id is None) or (season_name is None and season_id is None):
        return removed
    for competicao in data["competitions"]:
        if competicao["name"] == comp_name or competicao['wyId'] == comp_id:
            for temporada in competicao["seasons"]:
                if temporada["name"] == season_name or temporada['wyId'] == season_id:
                    competicao["seasons"].remove(temporada)
                    removed = True
                    break
            if len(competicao["seasons"]) == 0:
                data["competitions"].remove(competicao)
            break
    return removed


def print_menu(stdscr,menu,select_row_id):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    for id, row in enumerate(menu):
        x = w//2 - len(row)//2
        y = h//2 - len(menu)//2 + id
        if id == select_row_id:
            stdscr.attron(curses.color_pair(1))
            stdscr.addstr(y, x, row)
            stdscr.attroff(curses.color_pair(1))
        elif id == 0:
            stdscr.attron(curses.color_pair(2))
            stdscr.addstr(y, x, row)
            stdscr.attroff(curses.color_pair(2))
        else:
            stdscr.addstr(y, x, row)

    stdscr.refresh()

def list_seasons(filename, comp_name):
    dict = json.load(open(filename))
    string = f"""Seasons
------------------------"""
    comps = dict['competitions']
    seasons = []
    for comp in comps:
        if comp['name'] == comp_name:
            seasons = comp['seasons']
    for season in seasons:
            string += f"""
ID: {season['wyId']} | NAME: {season['name']} | START: {season['start']} | END: {season['end']}"""
    return string


def add_seasons(stdscr, request_file, comp_name,comp_id):
    filename = competitions_requests_folder + "/" + request_file
    dict = json.load(open(filename))

    current_row_id = 1
    menu = [f'[Adicionar] Seasons de {comp_name} de {request_file}']
    menu.append("Adicionar season nova por nome")
    menu.append("Adicionar season nova por id")
    menu.append("Voltar")
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #Voltar
                break
            elif current_row_id == len(menu)-2: #Adicionar season por id
                season_id = my_raw_input(stdscr, 0, 0, "Id da temporada:").decode('utf-8')
                season = {
                    'wyId' : season_id
                }
                verificao = verifica_temporada(comp_id,season)
                if verificao:
                    add_temporada(dict,season,comp_name=comp_name)
                    json.dump(dict,open(filename,'w'),indent=4)
                    stdscr.clear()
                    stdscr.addstr(0,0,"Temporada adicionada com sucesso!")
                    stdscr.refresh()
                    stdscr.getch()
                else:
                    stdscr.clear()
                    stdscr.addstr(0,0,"Erro ao adicionar temporada nova")
                    stdscr.refresh()
                    stdscr.getch()
            elif current_row_id == len(menu)-3: #Adicionar season por nome
                season_name = my_raw_input(stdscr, 0, 0, "Data da temporada (ex. 2023/2024):").decode('utf-8')
                season = {
                    'name' : season_name
                }
                verificao = verifica_temporada(comp_id,season)
                if verificao:
                    add_temporada(dict,season,comp_name=comp_name)
                    json.dump(dict,open(filename,'w'),indent=4)
                    stdscr.clear()
                    stdscr.addstr(0,0,"Temporada adicionada com sucesso!")
                    stdscr.refresh()
                    stdscr.getch()
                else:
                    stdscr.clear()
                    stdscr.addstr(0,0,"Erro ao adicionar temporada nova")
                    stdscr.refresh()
                    stdscr.getch()

        print_menu(stdscr, menu, current_row_id)
        stdscr.refresh()



def remove_seasons(stdscr, request_file, comp_name):
    filename = competitions_requests_folder + "/" + request_file
    dict = json.load(open(filename))
    comps = dict['competitions']
    seasons = []
    for comp in comps:
        if comp['name'] == comp_name:
            seasons = comp['seasons']
    current_row_id = 1
    menu = [f'[Remover] Seasons de {comp_name} de {request_file}']
    menu += [season['name'] for season in seasons]
    menu.append("Remover todas")
    menu.append("Voltar")
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #Voltar
                break
            elif current_row_id == len(menu)-2: #Remover todas
                remover_competicao(dict,comp_name=comp_name)
                json.dump(dict,open(filename,'w'),indent=4)
                break
            else:
                remover_temporada(dict,comp_name=comp_name,season_name=menu[current_row_id])
                json.dump(dict,open(filename,'w'),indent=4)
                break

        print_menu(stdscr, menu, current_row_id)
        stdscr.refresh()

def remove_comps(stdscr, request_file):
    filename = competitions_requests_folder + "/" + request_file
    dict = json.load(open(filename))
    comps = dict['competitions']
    current_row_id = 1
    menu = [f'Competições de {request_file}']
    menu += [comp['name'] for comp in comps]
    menu.append("Voltar")
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #EXIT
                break
            else:
                remove_seasons(stdscr,request_file, menu[current_row_id])
                break

        print_menu(stdscr, menu, current_row_id)
        stdscr.refresh()

def add_comps(stdscr, request_file):
    filename = competitions_requests_folder + "/" + request_file
    dict = json.load(open(filename))
    comps = dict['competitions']
    current_row_id = 1
    menu = [f'Competições de {request_file}']
    menu += [comp['name'] for comp in comps]
    menu.append("Adicionar nova competição por id")
    menu.append("Adicionar nova competição por nome")
    menu.append("Voltar")
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #EXIT
                break
            elif current_row_id == len(menu)-2: #Adicionar nova competiçao
                stdscr.clear()
                stdscr.addstr(0, 0, "Informações da nova competição")
                area = my_raw_input(stdscr, 1, 0, "Área:").decode('utf-8')
                comp_name = my_raw_input(stdscr, 3, 0, "Nome da competição:").decode('utf-8')
                custom_name = my_raw_input(stdscr, 5, 0, "Custom Name (Não obrigatório):").decode('utf-8')
                competition = {
                    "name": comp_name,
                    "area": area,
                    "custom_name": custom_name,
                    "tm_code": custom_name,
                    "seasons" : []
                }
                verificacao = verifica_competicao(competition)
                if verificacao:
                    add_competicao(dict,competition)
                    json.dump(dict,open(filename,'w'),indent=4)
                    stdscr.clear()
                    stdscr.addstr(0,0,"Competição adicionada com sucesso!")
                    stdscr.refresh()
                    stdscr.getch()
                else:
                    stdscr.clear()
                    stdscr.addstr(0,0,"Erro! Falha ao adicionar competição. Area/Nome inválidos")
                    stdscr.refresh()
                    stdscr.getch()
                break
            elif current_row_id == len(menu)-3: #Adicionar nova competiçao
                stdscr.clear()
                stdscr.addstr(0, 0, "Informações da nova competição")
                id = my_raw_input(stdscr, 1, 0, "Id da competição:").decode('utf-8')
                custom_name = my_raw_input(stdscr, 3, 0, "Custom Name (Não obrigatório):").decode('utf-8')
                competition = {
                    "wyId": id,
                    "custom_name": custom_name,
                    "tm_code": custom_name,
                    "seasons" : []
                }
                verificacao = verifica_competicao(competition)
                if verificacao:
                    add_competicao(dict,competition)
                    json.dump(dict,open(filename,'w'),indent=4)
                    stdscr.clear()
                    stdscr.addstr(0,0,"Competição adicionada com sucesso!")
                    stdscr.refresh()
                    stdscr.getch()
                else:
                    stdscr.clear()
                    stdscr.addstr(0,0,"Erro! Falha ao adicionar competição. Id inválido.")
                    stdscr.refresh()
                    stdscr.getch()
                break
            else:
                comp_id = ""
                for comp in comps:
                    if comp['name'] == menu[current_row_id]:
                        comp_id = comp['wyId']
                add_seasons(stdscr, request_file, menu[current_row_id],comp_id)
                break

        print_menu(stdscr, menu, current_row_id)
        stdscr.refresh()


def list_comps(stdscr, request_file):
    filename = competitions_requests_folder + "/" + request_file
    dict = json.load(open(filename))
    comps = dict['competitions']
    current_row_id = 1
    menu = [f'Competições de {request_file}']
    menu += [comp['name'] for comp in comps]
    menu.append("Voltar")
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #EXIT
                break
            else:
                string = list_seasons(filename, menu[current_row_id])

                stdscr.clear()
                stdscr.addstr(0,0, string) 
                stdscr.refresh()
                stdscr.getch()

        print_menu(stdscr, menu, current_row_id)
        stdscr.refresh()

def list_menu(stdscr):
    current_row_id = 1
    menu = ['Request Files']
    menu += requests_files
    menu.append("Voltar")
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #EXIT
                break
            else:
                list_comps(stdscr, menu[current_row_id])

        print_menu(stdscr, menu, current_row_id)
        stdscr.refresh()

def remove_menu(stdscr):
    current_row_id = 1
    menu = ['Request Files']
    menu += requests_files
    menu.append("Voltar")
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #EXIT
                break
            else:
                remove_comps(stdscr, menu[current_row_id])
                break

        print_menu(stdscr, menu, current_row_id)
        stdscr.refresh()

def add_menu(stdscr):
    current_row_id = 1
    menu = ['Request Files']
    menu += requests_files
    menu.append("Voltar")
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #EXIT
                break
            else:
                add_comps(stdscr, menu[current_row_id])
                break

        print_menu(stdscr, menu, current_row_id)
        stdscr.refresh()

def main_menu(stdscr):
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)

    current_row_id = 1
    menu = ['Menu','Listar', 'Adicionar', 'Remover', 'Exit']
    print_menu(stdscr, menu, current_row_id)

    while 1:
        key = stdscr.getch()
        stdscr.clear()

        if key == curses.KEY_UP and current_row_id > 1:
            current_row_id -= 1
        elif key == curses.KEY_DOWN and current_row_id < len(menu) - 1:
            current_row_id += 1
        elif key == curses.KEY_ENTER or key in [10,13]:
            if current_row_id == len(menu)-1: #EXIT
                break
            elif current_row_id == 1: #Listar
                list_menu(stdscr)
            elif current_row_id == 2: #Adicionar
                add_menu(stdscr)
            elif current_row_id == 3: #Remover
                remove_menu(stdscr)

        print_menu(stdscr,menu, current_row_id)
        stdscr.refresh()


if __name__ == '__main__':
    args = parse_arguments()
    if (args.list and args.add) or (args.list and args.remove) or (args.add and args.remove):
        print("Erro. Apenas pode utilizar um comando list/add/rem por vez.")
        exit()
    if args.comp_id and args.comp:
        print("Erro. Não pode utilizar -comp_id e -comp no mesmo comando.")
        exit()
    if args.season_id and args.season:
        print("Erro. Não pode utilizar -season e -season_id no mesmo comando.")
        exit()
    if args.add and args.comp and not (args.area or args.season or args.season_id):
        print("Erro. Para utilizar o comando add com o -comp tem de especificar a area com -area ou escolher uma season com -season_id, -season se a competição já estiver adicionada.")
        exit()
    if args.add and args.area and not args.comp:
        print("Erro. Para utilizar o comando add com o -area tem de especificar o nome da competição com -comp.")
        exit()
    if args.area and args.comp_id:
        print("Erro. Com o -comp_id não é premitido utilizar o -area.")
    if args.area and (args.list or args.remove):
        print("Erro. -area não pode ser utilizado com os comandos list/remove.")
    if args.custom_name and (args.list or args.remove):
        print("Erro. -custom_name não pode ser utilizado com os comandos list/remove.")
    if args.request_file:
        if not (args.list or args.add or args.remove):
            print("Erro. Tem de utilizar pelo menos um comando list/add/rem sobre o ficheiro")
            exit()
        filename = competitions_requests_folder + "/" + args.request_file[0]
        data = json.load(open(filename))
        competitions = data['competitions']
        comps_ids = [c['wyId'] for c in competitions]
        comps_names = [c['name'] for c in competitions]

        if args.list:
            #Listar
            competition = None
            if args.comp_id: #Listar a competicao por id
                for comp in competitions:
                    if comp['wyId'] == int(args.comp_id[0]):
                        competition = comp
                        break
                if competition == None:
                    print("Erro. Id de competição não encontrado!")
                    exit()
            elif args.comp:
                for comp in competitions:
                    if comp['name'] == args.comp[0]:
                        competition = comp
                        break
                if competition == None:
                    print("Erro. Nome de competição não encontrado!")
                    exit()
            if competition is None:
                #Listar tudo
                print(f"Competições de {args.request_file[0]}")
                print(f"-------------------------------------")
                for competition in competitions:
                    comp_name = competition['name']
                    wyId = competition['wyId']
                    area = competition['area']
                    custom_name = competition['custom_name']
                    print(f"Nome da competição: {comp_name}")
                    print(f"wyId: {wyId}")
                    print(f"Área: {area}")
                    print(f"Custom Name: {custom_name}")
                    print("***Seasons***")
                    for season in competition['seasons']:
                        season_name = season['name']
                        season_id = season['wyId']
                        season_start = season['start']
                        season_end = season['end']
                        print(f"    Season: {season_name}")
                        print(f"    Season wyId: {season_id}")
                        print(f"    Start Date: {season_start}")
                        print(f"    End Date: {season_end}")
                        print("*****")
                    print(f"-------------------------------------")
            else:
                season = None
                if args.season_id: #Listar season da competicao
                    for s in competition['seasons']:
                        if s['wyId'] == args.season_id[0]:
                            season = s
                            break
                    if season == None:
                        print("Erro. Season id não encontrada!")
                        exit()
                elif args.season: #Listar season da competicao
                    for s in competition['seasons']:
                        if s['name'] == args.season[0]:
                            season = s
                            break
                    if season == None:
                        print("Erro. Season não encontrada!")
                        exit()
                if season is None: #Listar toda a competicao por id
                    comp_name = competition['name']
                    wyId = competition['wyId']
                    area = competition['area']
                    custom_name = competition['custom_name']
                    print(f"Nome da competição: {comp_name}")
                    print(f"wyId: {wyId}")
                    print(f"Área: {area}")
                    print(f"Custom Name: {custom_name}")
                    print("***Seasons***")
                    for season in competition['seasons']:
                        season_name = season['name']
                        season_id = season['wyId']
                        season_start = season['start']
                        season_end = season['end']
                        print(f"    Season: {season_name}")
                        print(f"    Season wyId: {season_id}")
                        print(f"    Start Date: {season_start}")
                        print(f"    End Date: {season_end}")
                        print("*****")
                else:
                    season_name = season['name']
                    season_id = season['wyId']
                    season_start = season['start']
                    season_end = season['end']
                    print(f"Season: {season_name}")
                    print(f"Season wyId: {season_id}")
                    print(f"Start Date: {season_start}")
                    print(f"End Date: {season_end}")

        if args.remove:
            #Remover
            if args.comp:
                comp_name = args.comp[0]
                if args.season:
                    season_name = args.season[0]
                    if remover_temporada(data,comp_name=comp_name,season_name=season_name):
                        print("Removida temporada com sucesso!")
                    else:
                        print("Erro ao remover a temporada!")
                elif args.season_id:
                    season_id = args.season_id[0]
                    if remover_temporada(data,comp_name=comp_name,season_id=season_id):
                        print("Removida temporada com sucesso!")
                    else:
                        print("Erro ao remover a temporada!")
                else:
                    if remover_competicao(data,comp_name=comp_name):
                        print("Removido competição com sucesso!")
                    else:
                        print("Erro ao remover a competição!")
            elif args.comp_id:
                comp_id = int(args.comp_id[0])
                if args.season:
                    season_name = args.season[0]
                    if remover_temporada(data,comp_id=comp_id,season_name=season_name):
                        print("Removida temporada com sucesso!")
                    else:
                        print("Erro ao remover a temporada!")
                elif args.season_id:
                    season_id = args.season_id[0]
                    if remover_temporada(data,comp_id=comp_id,season_id=season_id):
                        print("Removida temporada com sucesso!")
                    else:
                        print("Erro ao remover a temporada!")
                else:
                    if remover_competicao(data,comp_id=comp_id):
                        print("Removido competição com sucesso!")
                    else:
                        print("Erro ao remover a competição!")
            else:
                print("Erro. Tem de utilizar -comp ou -comp_id com o comando remove.")
                exit()
        if args.add: #Adicionar
            if args.comp:
                comp_name = args.comp[0]
                if comp_name in comps_names: #Já existe a competição:
                    season = {}
                    if args.season: #Add season by name
                        season = {"name" : args.season[0]}
                    elif args.season_id: #Add season by id
                        season = {"wyId" : args.season_id[0]}
                    #Econtrar comp_id
                    comp_id = ""
                    for competition in competitions:
                        if competition['name'] == comp_name:
                            comp_id = competition['wyId']
                    if verifica_temporada(comp_id,season): #Verificar se temporada faz sentido
                        add_temporada(data,season,comp_id=int(args.comp_id[0])) #Adicionar a temporada
                    else:
                        print("Erro ao adicionar temporada. ")
                else:
                    comp_name = args.comp[0]
                    if args.area:
                        comp_area = args.area[0]
                    else:
                        print("Erro. Competição ainda não adicionada, se quiser usar -comp tem de utilizar -area.")
                        exit()
                    custom_name = args.custom_name[0] if args.custom_name else ""
                    comp = {
                        "name" : comp_name,
                        "area" : comp_area,
                        "custom_name" : custom_name,
                        "seasons" : []
                    }
                    if verifica_competicao(comp):
                        print("Competição adicionada com sucesso!")
                        add_competicao(data,comp)
                        if args.season or args.season_id:
                            season = {}
                            if args.season: #Add season by name
                                season = {"name" : args.season[0]}
                            elif args.season_id: #Add season by id
                                season = {"wyId" : args.season_id[0]}
                            #Econtrar comp_id
                            comp_id = ""
                            for competition in competitions:
                                if competition['name'] == comp_name:
                                    comp_id = competition['wyId']
                            if verifica_temporada(comp_id,season): #Verificar se temporada faz sentido
                                print("Temporada adicionada com sucesso!")
                                add_temporada(data,season,comp_id=comp_id) #Adicionar a temporada
                            else:
                                print("Erro ao adicionar temporada. ")
                    else:
                        print("Erro. Nome de competição ou área inválidos!")
            elif args.comp_id:
                comp_id = int(args.comp_id[0])
                if comp_id in comps_ids: #Já existe a competição:
                    season = {}
                    if args.season: #Add season by name
                        season = {"name" : args.season[0]}
                    elif args.season_id: #Add season by id
                        season = {"wyId" : args.season_id[0]}

                    if verifica_temporada(comp_id,season): #Verificar se temporada faz sentido
                        print("Temporada adicionada com sucesso!")
                        add_temporada(data,season,comp_id=comp_id) #Adicionar a temporada
                    else:
                        print("Erro ao adicionar temporada. ")
                else: #Adiciona a competição
                    custom_name = args.custom_name[0] if args.custom_name else ""
                    comp = {
                        "wyId" : comp_id,
                        "custom_name" : custom_name,
                        "seasons" : []
                    }
                    if verifica_competicao(comp):
                        print("Competição adicionada com sucesso!")
                        add_competicao(data,comp) #Adiciona competição

                        if args.season or args.season_id:
                            #Verifica se é para adicionar temporada
                            season = {}
                            if args.season: #Add season by name
                                season = {"name" : args.season[0]}
                            elif args.season_id: #Add season by id
                                season = {"wyId" : args.season_id[0]}

                            if verifica_temporada(comp_id,season): #Verificar se temporada faz sentido
                                print("Temporada adicionada com sucesso!")
                                add_temporada(data,season,comp_id=comp_id) #Adicionar a temporada
                            else:
                                print("Erro ao adicionar temporada.")
                    else:
                        print("Erro. Id de competição inválido!")
            else:
                print("Erro. Tem de utilizar -comp ou -comp_id com o comando add.")
                exit()
        json.dump(data,open(filename,'w'),indent=4)
    else:
        curses.wrapper(main_menu)