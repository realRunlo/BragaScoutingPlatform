DELETE FROM scouting.match_event_carry 
WHERE "match" IN (
  SELECT idmatch from scouting."match" 
  WHERE competition_season in (%replace%)
);


DELETE FROM scouting.match_event_infraction 
WHERE "match" IN (
  SELECT idmatch from scouting."match" 
  WHERE competition_season in (%replace%)
);

DELETE FROM scouting.match_event_other 
WHERE "match" IN (
  SELECT idmatch from scouting."match" 
  WHERE competition_season in (%replace%)
);


DELETE FROM scouting.match_event_pass 
WHERE "match" IN (
  SELECT idmatch from scouting."match" 
  WHERE competition_season in (%replace%)
);


DELETE FROM scouting.match_event_shot 
WHERE "match" IN (
  SELECT idmatch from scouting."match" 
  WHERE competition_season in (%replace%)
);


DELETE FROM scouting.match_lineup_player_position 
WHERE match_lineup_id IN (
  SELECT match_lineup_id from scouting.match_lineup 
  WHERE "match" IN (
    SELECT idmatch FROM scouting."match"
      WHERE competition_season in (%replace%)
  )
);


DELETE FROM scouting.match_lineup 
  WHERE "match" IN (
    SELECT idmatch FROM scouting."match"
      WHERE competition_season in (%replace%)
);


DELETE FROM scouting.match_substitution
  WHERE "match" IN (
    SELECT idmatch FROM scouting."match"
      WHERE competition_season in (%replace%)
);


DELETE FROM scouting.match_formation
  WHERE "match" IN (
    SELECT idmatch FROM scouting."match"
      WHERE competition_season in (%replace%)
);

DELETE FROM scouting.player_match_stats
  WHERE "match" IN (
    SELECT idmatch FROM scouting."match"
      WHERE competition_season in (%replace%)
);



DELETE FROM scouting."match"
  WHERE competition_season in (%replace%);


DELETE FROM scouting.team_competition_season_round
  WHERE competition_season_round IN (
    SELECT csr.idcompetition_season_round FROM scouting.competition_season_round csr
      where csr.competition_season in (%replace%)
);

DELETE FROM scouting.competition_season_round_group
  WHERE competition_season_round IN (
    SELECT csr.idcompetition_season_round FROM scouting.competition_season_round csr
      where csr.competition_season in (%replace%)
);


DELETE FROM scouting.competition_season_round
  WHERE competition_season in (%replace%);


DELETE FROM scouting.player_positions
  WHERE team_competition_season IN (
    SELECT tcs.idteam_competition_season from scouting.team_competition_season tcs
      where tcs.competition_season in (%replace%)
);

DELETE FROM scouting.career_entry
  where team_competition_season IN (
    SELECT tcs.idteam_competition_season from scouting.team_competition_season tcs
      where tcs.competition_season in (%replace%)
);


DELETE FROM scouting.team_competition_season
  WHERE competition_season in (%replace%);


DELETE FROM scouting.competition_season
  WHERE idcompetition_season in (%replace%);


DELETE FROM scouting.team where idteam not in (select team from scouting.team_competition_season);

DELETE FROM scouting.player where idplayer not in (select player from scouting.career_entry);




