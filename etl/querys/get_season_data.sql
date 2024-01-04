/*Description: Get season data from database*/



/*-------------- COMPETITION DATA --------------*/

/*Get competitions data from database*/
select * from scouting.competition
where idcompetitions in (
  select competition from scouting.competition_season
  where idcompetition_season in (%replace%)
);

/*Get competition season data from database*/
select * from scouting.competition_season
where idcompetition_season in (%replace%);

/*Get competition season round data from database*/
select * from scouting.competition_season_round
where competition_season in (%replace%);

/*Get competition season round group data from database*/
select * from scouting.competition_season_round_group
where competition_season_round in (
  select idcompetition_season_round from scouting.competition_season_round
  where competition_season in (%replace%)
);

/*Get scorers data from database*/
select * from scouting.competition_season_scorer
where competition_season in (%replace%);

/*Get assistmans data from database*/
select * from scouting.competition_season_assistman
where competition_season in (%replace%);

/*-------------- TEAM DATA --------------*/

/*Get teams data from database*/
select * from scouting.team
where idteam in (
  select team from scouting.team_competition_season
  where competition_season in (%replace%)
);


/*Get team competition season data from database*/
select * from scouting.team_competition_season
where competition_season in (%replace%);

/*Get team competition season round data from database*/
select * from scouting.team_competition_season_round
where competition_season_round in (
  select idcompetition_season_round from scouting.competition_season_round
  where competition_season in (%replace%)
);

/*-------------- PLAYER DATA --------------*/

/*Get players data from database*/
select * from scouting.player
where idplayer in (
  select player from scouting.career_entry
  where team_competition_season in (
    select idteam_competition_season from scouting.team_competition_season
    where competition_season in (%replace%)
  )
);

/*Get player positions data from database*/
select * from scouting.player_positions
where team_competition_season in (
  select idteam_competition_season from scouting.team_competition_season
  where competition_season in (%replace%)
);

/*Get career entry data from database*/
select * from scouting.career_entry
where team_competition_season in (
  select idteam_competition_season from scouting.team_competition_season
  where competition_season in (%replace%)
);

/*-------------- MATCH DATA --------------*/

/*Get matches data from database*/
select * from scouting."match"
where competition_season in (%replace%);

/*Get match formation data from database*/
select * from scouting.match_formation
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match lineup data from database*/
select * from scouting.match_lineup
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match substitution data from database*/
select * from scouting.match_substitution
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match lineup position data from database*/
select * from scouting.player_match_stats
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match player stats data from database*/
select * from scouting.player_match_stats
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match carry events data from database*/
select * from scouting.match_event_carry
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match pass events data from database*/
select * from scouting.match_event_pass
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match shot events data from database*/
select * from scouting.match_event_shot
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match other events data from database*/
select * from scouting.match_event_other
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);

/*Get match infractions events data from database*/
select * from scouting.match_event_infraction
where match in (
  select idmatch from scouting."match"
  where competition_season in (%replace%)
);