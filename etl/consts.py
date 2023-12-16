## table parameters

### misc tables
area_key_parameters = ['idareas']
area_parameters     = ['idareas', 'name', 'alpha3code']

### competitions tables
competition_key_parameters = ['idcompetitions']
competition_parameters     = ['idcompetitions','name','area','gender','type',
                              'format','divisionLevel','category','custom_name']

competition_season_key_parameters = ['idcompetition_season']
competition_season_parameters     = ['idcompetition_season','startDate','endDate',
                                     'name','competition']

competition_season_round_key_parameters = ['idcompetition_season_round']
competition_season_round_parameters     = ['idcompetition_season_round','competition_season',
                                           'startDate','endDate','name','type']

competition_season_round_group_key_parameters = ['idgroup']
competition_season_round_group_parameters     = ['idgroup','competition_season_round','group_name']

### teams tables
team_key_parameters = ['idteam']
team_parameters     = ['idteam','name','official_name','icon','gender','type','city','category','area']

team_competition_season_key_parameters = ['competition_season','team']
team_competition_season_parameters     = ['competition_season','team']

team_competition_season_round_key_parameters = ['competition_season_round','team']
team_competition_season_round_parameters     = ['competition_season_round','team','totalDraws','totalGoalsAgainst',
                                                'totalGoalsFor','totalLosses','totalPlayed','totalPoints','totalWins',
                                                'rank','group_id']

### players tables
player_key_parameters   = ['idplayer']
player_parameters       = ['idplayer','name','short_name','passport_area','birth_area','birth_date','image',
                            'foot','height','weight','status','gender','role_code2','role_code3','role_name',
                            'market_value','contract_expiration','contract_agency','current_team','currency']

career_entry_key_parameters = ['player','team_competition_season']
career_entry_parameters     = ['player','team_competition_season','appearances','goal','minutesPlayed',
                               'penalties','redCards','shirtNumber','substituteIn','substituteOnBench',
                               'substituteOut','yellowCard','team','competition_season']

player_positions_key_parameters = ['player','code','team_competition_season']
player_positions_parameters     = ['player','percent','code','name','team_competition_season']

### matches tables
match_key_parameters = ['idmatch']
match_parameters     = ['idmatch', 'competition_season','round', 'home_team', 'away_team', 'date', 'home_score',
                        'away_score', 'winner', 'duration', 'home_score_et', 'home_score_ht', 'home_score_p',
                        'away_score_et', 'away_score_ht', 'away_score_p','home_shots', 'away_shots',
                        'home_shotsOnTarget', 'away_shotsOnTarget', 'home_xg', 'away_xg', 'home_attacks_total',
                        'away_attacks_total', 'home_corners', 'away_corners', 'home_possessionPercent',
                        'away_possessionPercent', 'home_fouls', 'away_fouls', 'home_pass_successful_percent',
                        'away_pass_successful_percent', 'home_vertical_pass_successful_percent',
                        'away_vertical_pass_successful_percent', 'home_offsides', 'away_offsides',
                        'home_clearances', 'away_clearances', 'home_interceptions', 'away_interceptions',
                        'home_tackles', 'away_tackles']



player_match_stats_key_parameters = ['match', 'player']
player_match_stats_parameters     = ['match', 'player', 'offensiveDuels', 'progressivePasses', 'forwardPasses', 
                                     'crosses', 'keyPasses', 'defensiveDuels', 'interceptions', 'recoveries',
                                     'successfulPasses', 'longPasses', 'aerialDuels', 'losses', 'ownHalfLosses', 
                                     'goalKicks', 'receivedPass', 'dribbles', 'touchInBox', 'opponentHalfRecoveries',
                                     'position']

match_lineup_key_parameters = ['match', 'team', 'period', 'second']
match_lineup_parameters     = ['match', 'team', 'period', 'second', 'lineup']

match_lineup_player_position_key_parameters = ['match_lineup_id', 'player']
match_lineup_player_position_parameters     = ['match_lineup_id', 'player', 'position']
    
match_formation_key_parameters = ['match', 'player']
match_formation_parameters     = ['match', 'player', 'assists', 'goals', 'ownGoals', 'redCards', 'shirtNumber',
                                  'yellowCards', 'team', 'type']

match_substitution_key_parameters = ['match', 'playerIn', 'playerOut']
match_substitution_parameters     = ['match', 'playerIn', 'playerOut', 'team', 'minute']

match_event_other_key_parameters = ['idmatch_event']
match_event_other_parameters     = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y', 'minute', 'second','team']

match_event_pass_key_parameters = ['idmatch_event']
match_event_pass_parameters     = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y',
                                   'minute', 'second', 'accurate', 'recipient', 'endlocation_x', 'endlocation_y','team']

match_event_shot_key_parameters = ['idmatch_event']
match_event_shot_parameters     = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y',
                                   'minute', 'second', 'isGoal', 'onTarget', 'xg', 'postShotXg','team']

match_event_carry_key_parameters = ['idmatch_event']
match_event_carry_parameters     = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y',
                                    'minute', 'second', 'endlocation_x', 'endlocation_y','team']

match_event_infraction_key_parameters = ['idmatch_event']
match_event_infraction_parameters     = ['idmatch_event', 'match', 'player', 'matchPeriod', 'location_x', 'location_y',
                                         'minute', 'second', 'yellowCard', 'redCard','team']

match_goals_key_parameters = ['match_event']
match_goals_parameters     = ['match_event', 'match','scorer','minute','second','assistant','assist_minute','assist_second','team']