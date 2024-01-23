--
-- PostgreSQL database dump
--

-- Dumped from database version 12.16
-- Dumped by pg_dump version 16.1

-- Started on 2024-01-23 11:06:44

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 8 (class 2615 OID 24853)
-- Name: scouting; Type: SCHEMA; Schema: -; Owner: scoutAdmin
--

CREATE SCHEMA scouting;


ALTER SCHEMA scouting OWNER TO "scoutAdmin";

--
-- TOC entry 253 (class 1255 OID 24854)
-- Name: get_group_id(integer, integer); Type: FUNCTION; Schema: scouting; Owner: scoutAdmin
--

CREATE FUNCTION scouting.get_group_id(arg_team integer, arg_round integer) RETURNS integer
    LANGUAGE plpgsql
    AS $$
DECLARE 
    group_id_value int;
BEGIN
    SELECT group_id INTO group_id_value
    FROM scouting.team_competition_season_round
    WHERE team = arg_team AND competition_season_round = arg_round;

    RETURN group_id_value;
END;
$$;


ALTER FUNCTION scouting.get_group_id(arg_team integer, arg_round integer) OWNER TO "scoutAdmin";

--
-- TOC entry 254 (class 1255 OID 24855)
-- Name: match_update_group_id(); Type: FUNCTION; Schema: scouting; Owner: scoutAdmin
--

CREATE FUNCTION scouting.match_update_group_id() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.group := scouting.get_group_id(NEW.home_team, NEW.round);
    RETURN NEW;
END;
$$;


ALTER FUNCTION scouting.match_update_group_id() OWNER TO "scoutAdmin";

--
-- TOC entry 255 (class 1255 OID 24856)
-- Name: on_substitution_insert(); Type: FUNCTION; Schema: scouting; Owner: scoutAdmin
--

CREATE FUNCTION scouting.on_substitution_insert() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    formation_player_to_update scouting.match_formation;
BEGIN
	-- Update formation player
	-- get player in formation
	SELECT * INTO formation_player_to_update 
    FROM scouting.match_formation 
    WHERE "match" = NEW."match" AND "player" = NEW."playerIn" 
    LIMIT 1;

    -- Check if the player is found in the formation
    IF FOUND THEN
        -- Update the type to 'substituted'
        UPDATE scouting.match_formation
        SET type = 'substituted'
        WHERE "match" = NEW."match" AND "player" = NEW."playerIn";
    END IF;
	
	-- Get players and team images
	select image from scouting.player where idplayer = NEW."playerIn" into NEW."playerInImage";
	select image from scouting.player where idplayer = NEW."playerOut" into NEW."playerOutImage";
	select icon from scouting.team where idteam = NEW."team" into NEW."teamImage";
	
	
    RETURN NEW;
END;
$$;


ALTER FUNCTION scouting.on_substitution_insert() OWNER TO "scoutAdmin";

--
-- TOC entry 257 (class 1255 OID 33172)
-- Name: update_career_entry_position(); Type: FUNCTION; Schema: scouting; Owner: scoutAdmin
--

CREATE FUNCTION scouting.update_career_entry_position() RETURNS trigger
    LANGUAGE plpgsql
    AS $$BEGIN
	UPDATE scouting.career_entry
	SET
		position_name = NEW.name,
		position_code = NEW.code,
		position_percent = NEW.percent
	WHERE
		player = NEW.player 
		AND team_competition_season = NEW.team_competition_season
		AND (position_percent is null OR NEW.percent > position_percent);
	 RETURN NEW;
END;$$;


ALTER FUNCTION scouting.update_career_entry_position() OWNER TO "scoutAdmin";

--
-- TOC entry 256 (class 1255 OID 24857)
-- Name: update_match_formation_competition_season(); Type: FUNCTION; Schema: scouting; Owner: scoutAdmin
--

CREATE FUNCTION scouting.update_match_formation_competition_season() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    match_reference scouting.match;
BEGIN
    -- get player in formation
    SELECT * INTO match_reference 
    FROM scouting.match 
    WHERE "idmatch" = NEW.match 
    LIMIT 1;

    -- Check if the player is found in the formation
    IF FOUND THEN
        NEW.competition_season = match_reference."competition_season";
    END IF;

    RETURN NEW;
END;
$$;


ALTER FUNCTION scouting.update_match_formation_competition_season() OWNER TO "scoutAdmin";

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 207 (class 1259 OID 24858)
-- Name: area; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.area (
    idareas integer NOT NULL,
    name text,
    alpha3code text
);


ALTER TABLE scouting.area OWNER TO "scoutAdmin";

--
-- TOC entry 208 (class 1259 OID 24864)
-- Name: career_entry; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.career_entry (
    player integer NOT NULL,
    team_competition_season integer NOT NULL,
    appearances integer,
    goal integer,
    "minutesPlayed" integer,
    penalties integer,
    "redCards" integer,
    "shirtNumber" integer,
    "substituteIn" integer,
    "substituteOnBench" integer,
    "substituteOut" integer,
    "yellowCard" integer,
    team integer,
    competition_season integer,
    position_name text DEFAULT 'undefined'::text,
    position_code text DEFAULT '-'::text,
    position_percent integer,
    aerial_duels_won_percent integer,
    successful_dribbles_percent real,
    successful_crosses_percent real,
    successful_passes_percent real,
    successful_long_passes_percent real,
    defensive_duels_won_percent real,
    offensive_duels_won_percent real,
    xg_shot real,
    shots integer,
    shots_on_target integer,
    shot_assists integer,
    progressive_run integer,
    successful_crosses integer,
    successful_forward_passes integer,
    successful_key_passes integer,
    successful_long_passes integer,
    successful_progressive_passes integer,
    aerial_duels_won integer,
    defensive_duels_won integer,
    offensive_duels_won integer,
    successful_dribbles integer,
    recoveries integer,
    opponent_half_recoveries integer,
    losses integer,
    own_half_losses integer,
    interceptions integer,
    touch_in_box integer,
    successful_passes integer,
    received_pass integer
);


ALTER TABLE scouting.career_entry OWNER TO "scoutAdmin";

--
-- TOC entry 209 (class 1259 OID 24867)
-- Name: competition; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.competition (
    idcompetitions integer NOT NULL,
    name text,
    area integer,
    gender text,
    type text,
    format text,
    "divisionLevel" integer,
    category text,
    custom_name text
);


ALTER TABLE scouting.competition OWNER TO "scoutAdmin";

--
-- TOC entry 210 (class 1259 OID 24873)
-- Name: competition_season; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.competition_season (
    idcompetition_season integer NOT NULL,
    competition integer,
    "startDate" date,
    "endDate" date,
    name text
);


ALTER TABLE scouting.competition_season OWNER TO "scoutAdmin";

--
-- TOC entry 241 (class 1259 OID 33090)
-- Name: competition_season_assistman; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.competition_season_assistman (
    competition_season integer NOT NULL,
    player integer NOT NULL,
    team integer NOT NULL,
    assists integer
);


ALTER TABLE scouting.competition_season_assistman OWNER TO "scoutAdmin";

--
-- TOC entry 212 (class 1259 OID 24913)
-- Name: match_formation; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_formation (
    match integer NOT NULL,
    player integer NOT NULL,
    team integer,
    assists integer,
    goals integer,
    "ownGoals" integer,
    "redCards" integer,
    "yellowCards" integer,
    type text,
    "shirtNumber" integer,
    competition_season integer
);


ALTER TABLE scouting.match_formation OWNER TO "scoutAdmin";

--
-- TOC entry 215 (class 1259 OID 24931)
-- Name: player; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.player (
    idplayer integer NOT NULL,
    name text,
    short_name text,
    birth_area integer,
    birth_date date,
    passport_area integer,
    image text,
    current_team integer,
    foot text,
    height integer,
    weight integer,
    status text,
    gender text,
    role_code2 text,
    role_code3 text,
    role_name text,
    market_value integer,
    contract_expiration date,
    contract_agency text,
    currency text,
    tm_scrap bit(1) DEFAULT '0'::"bit",
    tm_market_value integer,
    tm_market_value_currency text
);


ALTER TABLE scouting.player OWNER TO "scoutAdmin";

--
-- TOC entry 216 (class 1259 OID 24938)
-- Name: team; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.team (
    idteam integer NOT NULL,
    name text,
    official_name text,
    icon text,
    gender text,
    type text,
    city text,
    category text,
    area integer
);


ALTER TABLE scouting.team OWNER TO "scoutAdmin";

--
-- TOC entry 243 (class 1259 OID 33119)
-- Name: competition_season_assistmen_view; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.competition_season_assistmen_view AS
 SELECT csa.competition_season,
    csa.player,
    csa.team,
    csa.assists,
    p.short_name,
    p.image,
    t.name,
    t.icon,
    count(*) AS num_entries
   FROM (((scouting.competition_season_assistman csa
     JOIN scouting.player p ON ((csa.player = p.idplayer)))
     JOIN scouting.team t ON ((csa.team = t.idteam)))
     JOIN scouting.match_formation mf ON (((csa.competition_season = mf.competition_season) AND (csa.player = mf.player) AND (csa.team = mf.team) AND ((mf.type = 'lineup'::text) OR (mf.type = 'substituted'::text)))))
  GROUP BY csa.competition_season, csa.player, csa.team, csa.assists, p.short_name, p.image, t.name, t.icon;


ALTER VIEW scouting.competition_season_assistmen_view OWNER TO "scoutAdmin";

--
-- TOC entry 211 (class 1259 OID 24879)
-- Name: match; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match (
    idmatch integer NOT NULL,
    competition_season integer,
    home_team integer,
    away_team integer,
    date date,
    home_score integer,
    away_score integer,
    winner integer,
    round integer,
    "group" integer,
    duration text,
    home_score_et integer,
    home_score_ht integer,
    home_score_p integer,
    away_score_et integer,
    away_score_ht integer,
    away_score_p integer,
    home_shots integer DEFAULT 0,
    away_shots integer DEFAULT 0,
    "home_shotsOnTarget" integer DEFAULT 0,
    "away_shotsOnTarget" integer DEFAULT 0,
    home_xg real DEFAULT 0,
    away_xg real DEFAULT 0,
    home_attacks_total integer DEFAULT 0,
    away_attacks_total integer DEFAULT 0,
    home_corners integer DEFAULT 0,
    away_corners integer DEFAULT 0,
    "home_possessionPercent" integer DEFAULT 0,
    "away_possessionPercent" integer DEFAULT 0,
    home_fouls integer DEFAULT 0,
    away_fouls integer DEFAULT 0,
    home_pass_successful_percent real DEFAULT 0,
    away_pass_successful_percent real DEFAULT 0,
    home_vertical_pass_successful_percent real DEFAULT 0,
    away_vertical_pass_successful_percent real DEFAULT 0,
    home_offsides integer DEFAULT 0,
    away_offsides integer DEFAULT 0,
    home_clearances integer DEFAULT 0,
    away_clearances integer DEFAULT 0,
    home_interceptions integer DEFAULT 0,
    away_interceptions integer DEFAULT 0,
    home_tackles integer DEFAULT 0,
    away_tackles integer DEFAULT 0,
    away_clean_sheet bit(1) GENERATED ALWAYS AS ((
CASE
    WHEN (((home_score - home_score_p) - home_score_et) = 0) THEN 1
    ELSE 0
END)::bit(1)) STORED,
    home_clean_sheet bit(1) GENERATED ALWAYS AS ((
CASE
    WHEN (((away_score - away_score_p) - away_score_et) = 0) THEN 1
    ELSE 0
END)::bit(1)) STORED,
    "1st_period_end" integer DEFAULT 45,
    "2nd_period_end" integer DEFAULT 90,
    ex_period_end integer DEFAULT 120
);


ALTER TABLE scouting.match OWNER TO "scoutAdmin";

--
-- TOC entry 213 (class 1259 OID 24919)
-- Name: match_lineup; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_lineup (
    match integer NOT NULL,
    team integer NOT NULL,
    period text NOT NULL,
    match_lineup_id integer NOT NULL,
    lineup text,
    second integer NOT NULL
);


ALTER TABLE scouting.match_lineup OWNER TO "scoutAdmin";

--
-- TOC entry 214 (class 1259 OID 24925)
-- Name: match_lineup_player_position; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_lineup_player_position (
    match_lineup_id integer NOT NULL,
    player integer NOT NULL,
    "position" text NOT NULL
);


ALTER TABLE scouting.match_lineup_player_position OWNER TO "scoutAdmin";

--
-- TOC entry 217 (class 1259 OID 24944)
-- Name: competition_season_gk_stats; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.competition_season_gk_stats AS
 SELECT subquery.competition_season,
    subquery.player,
    subquery.name,
    subquery.total_games_played,
    subquery.total_clean_sheets,
    subquery.image AS player_image,
    t.icon AS team_icon,
    t.idteam AS team_id
   FROM (( SELECT mf.competition_season,
            mlp.player,
            p.short_name AS name,
            p.image,
            count(DISTINCT mf.match) AS total_games_played,
            count(DISTINCT
                CASE
                    WHEN (((ml.team = m.home_team) AND (m.home_clean_sheet = '1'::"bit")) OR ((ml.team = m.away_team) AND (m.away_clean_sheet = '1'::"bit"))) THEN m.idmatch
                    ELSE NULL::integer
                END) AS total_clean_sheets,
            mf.team
           FROM ((((scouting.match_formation mf
             JOIN scouting.match_lineup ml ON ((ml.match = mf.match)))
             JOIN scouting.match_lineup_player_position mlp ON (((mlp.match_lineup_id = ml.match_lineup_id) AND (mlp."position" = 'gk'::text) AND (mlp.player = mf.player))))
             JOIN scouting.player p ON ((p.idplayer = mlp.player)))
             LEFT JOIN scouting.match m ON ((m.idmatch = mf.match)))
          WHERE (mf.type = ANY (ARRAY['lineup'::text, 'substituted'::text]))
          GROUP BY mf.competition_season, mlp.player, p.short_name, p.image, mf.team) subquery
     JOIN scouting.team t ON ((subquery.team = t.idteam)));


ALTER VIEW scouting.competition_season_gk_stats OWNER TO "scoutAdmin";

--
-- TOC entry 218 (class 1259 OID 24949)
-- Name: competition_season_round; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.competition_season_round (
    idcompetition_season_round integer NOT NULL,
    competition_season integer,
    "startDate" date,
    "endDate" date,
    name text,
    type text
);


ALTER TABLE scouting.competition_season_round OWNER TO "scoutAdmin";

--
-- TOC entry 219 (class 1259 OID 24955)
-- Name: competition_season_round_group; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.competition_season_round_group (
    idgroup integer NOT NULL,
    competition_season_round integer,
    group_name text
);


ALTER TABLE scouting.competition_season_round_group OWNER TO "scoutAdmin";

--
-- TOC entry 240 (class 1259 OID 33070)
-- Name: competition_season_scorer; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.competition_season_scorer (
    competition_season integer NOT NULL,
    player integer NOT NULL,
    team integer NOT NULL,
    goals integer
);


ALTER TABLE scouting.competition_season_scorer OWNER TO "scoutAdmin";

--
-- TOC entry 242 (class 1259 OID 33114)
-- Name: competition_season_scorers_view; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.competition_season_scorers_view AS
 SELECT css.competition_season,
    css.player,
    css.team,
    css.goals,
    p.short_name,
    p.image,
    t.name,
    t.icon,
    count(*) AS games_played
   FROM (((scouting.competition_season_scorer css
     JOIN scouting.player p ON ((css.player = p.idplayer)))
     JOIN scouting.team t ON ((css.team = t.idteam)))
     JOIN scouting.match_formation mf ON (((css.competition_season = mf.competition_season) AND (css.player = mf.player) AND (css.team = mf.team) AND ((mf.type = 'lineup'::text) OR (mf.type = 'substituted'::text)))))
  GROUP BY css.competition_season, css.player, css.team, css.goals, p.short_name, p.image, t.name, t.icon;


ALTER VIEW scouting.competition_season_scorers_view OWNER TO "scoutAdmin";

--
-- TOC entry 234 (class 1259 OID 25037)
-- Name: player_positions; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.player_positions (
    percent integer,
    code text NOT NULL,
    name text,
    team_competition_season integer NOT NULL,
    player integer NOT NULL
);


ALTER TABLE scouting.player_positions OWNER TO "scoutAdmin";

--
-- TOC entry 244 (class 1259 OID 33162)
-- Name: correct_position_players; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.correct_position_players AS
 WITH rankedplayers AS (
         SELECT player_positions.team_competition_season,
            player_positions.player,
            player_positions.name,
            player_positions.percent,
            player_positions.code,
            row_number() OVER (PARTITION BY player_positions.team_competition_season, player_positions.player ORDER BY player_positions.percent DESC) AS rn
           FROM scouting.player_positions
        )
 SELECT rankedplayers.team_competition_season,
    rankedplayers.player,
    rankedplayers.name,
    rankedplayers.percent,
    rankedplayers.code
   FROM rankedplayers
  WHERE (rankedplayers.rn = 1);


ALTER VIEW scouting.correct_position_players OWNER TO "scoutAdmin";

--
-- TOC entry 220 (class 1259 OID 24966)
-- Name: current_seasons; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.current_seasons AS
 SELECT subquery.idcompetition_season,
    subquery.competition,
    subquery.competition_name,
    subquery.season_name
   FROM ( SELECT cs.competition,
            row_number() OVER (PARTITION BY cs.competition ORDER BY cs."startDate" DESC) AS rn,
            cs.idcompetition_season,
            c.name AS competition_name,
            cs.name AS season_name
           FROM ((scouting.competition_season cs
             JOIN scouting.competition c ON ((c.idcompetitions = cs.competition)))
             JOIN scouting.area a ON ((a.idareas = c.area)))) subquery
  WHERE (subquery.rn = 1);


ALTER VIEW scouting.current_seasons OWNER TO "scoutAdmin";

--
-- TOC entry 235 (class 1259 OID 25043)
-- Name: team_competition_season; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.team_competition_season (
    idteam_competition_season integer NOT NULL,
    team integer,
    competition_season integer,
    average_passes double precision,
    total_goals integer,
    total_conceded_goals integer,
    total_clean_sheets integer,
    total_matches integer,
    xg_shot double precision,
    xg_shot_against double precision,
    total_crosses integer,
    total_through_passes integer,
    total_fouls integer,
    total_red_cards integer,
    total_shots integer,
    total_shots_against integer,
    total_yellow_cards integer,
    total_progressive_run integer,
    percent_shots_on_target double precision
);


ALTER TABLE scouting.team_competition_season OWNER TO "scoutAdmin";

--
-- TOC entry 245 (class 1259 OID 41366)
-- Name: current_season_player_position; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.current_season_player_position AS
 SELECT subquery.idplayer,
    subquery.name,
    subquery.position_code,
    subquery.entries,
    subquery.position_rank
   FROM ( WITH allplayerpositions AS (
                 SELECT p.idplayer,
                    p.name,
                    ce.position_code,
                    COALESCE(round((((ce.position_percent * ce.appearances) / 100))::double precision), (0)::double precision) AS entries
                   FROM (((scouting.player p
                     JOIN scouting.career_entry ce ON ((p.idplayer = ce.player)))
                     JOIN scouting.team_competition_season tcs ON ((ce.team_competition_season = tcs.idteam_competition_season)))
                     JOIN scouting.current_seasons cs ON ((tcs.competition_season = cs.idcompetition_season)))
                ), playerpositions AS (
                 SELECT DISTINCT allplayerpositions.idplayer,
                    allplayerpositions.name,
                    allplayerpositions.position_code,
                    sum(allplayerpositions.entries) OVER (PARTITION BY allplayerpositions.idplayer, allplayerpositions.name, allplayerpositions.position_code) AS entries
                   FROM allplayerpositions
                )
         SELECT playerpositions.idplayer,
            playerpositions.name,
            playerpositions.position_code,
            (playerpositions.entries)::integer AS entries,
            row_number() OVER (PARTITION BY playerpositions.idplayer ORDER BY playerpositions.entries DESC) AS position_rank
           FROM playerpositions) subquery
  WHERE (subquery.position_rank = 1);


ALTER VIEW scouting.current_season_player_position OWNER TO "scoutAdmin";

--
-- TOC entry 232 (class 1259 OID 25032)
-- Name: player_match_stats; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.player_match_stats (
    idplayer_match_stats integer NOT NULL,
    match integer,
    player integer,
    "offensiveDuels" integer,
    "progressivePasses" integer,
    "forwardPasses" integer,
    crosses integer,
    "keyPasses" integer,
    "defensiveDuels" integer,
    interceptions integer,
    recoveries integer,
    "percent_successfulPasses" real,
    "longPasses" integer,
    "aerialDuels" integer,
    losses integer,
    "ownHalfLosses" integer,
    "opponentHalfRecoveries" integer,
    "goalKicks" integer,
    "receivedPass" integer,
    dribbles integer,
    "touchInBox" integer,
    "position" text,
    rating double precision DEFAULT 6.0,
    team integer,
    minutes_played integer DEFAULT 0,
    passes integer,
    "successfulPasses" integer
);


ALTER TABLE scouting.player_match_stats OWNER TO "scoutAdmin";

--
-- TOC entry 249 (class 1259 OID 49634)
-- Name: current_players; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.current_players AS
 WITH player_team_competition_season_rating AS (
         SELECT DISTINCT ON (subquery.competition_season, subquery.player, subquery.team) subquery.competition_season,
            subquery.player,
            avg(subquery.rating) OVER (PARTITION BY subquery.player, subquery.competition_season, subquery.team) AS mean_rating,
            subquery.team
           FROM ( SELECT m.competition_season,
                    pms.player,
                    pms.rating,
                    pms.team
                   FROM (scouting.player_match_stats pms
                     JOIN scouting.match m ON ((pms.match = m.idmatch)))) subquery
        )
 SELECT p.idplayer,
    p.name AS player_name,
    p.short_name AS player_short_name,
    p.market_value,
    p.foot,
    p.image,
    p.role_name,
    p.status,
    p.birth_area AS player_nationality_id,
    COALESCE(p.tm_market_value, NULL::integer) AS tm_market_value,
    team.name AS current_team_name,
    team.icon AS current_team_icon,
    area.name AS player_nationality_name,
    sum(ce."minutesPlayed") OVER (PARTITION BY ce.player, ce.team) AS minutes_player,
        CASE
            WHEN (area.name = 'Korea Republic'::text) THEN 'https://cdn.countryflags.com/thumbs/south-korea/flag-square-250.png'::text
            WHEN (area.name = 'United States'::text) THEN 'https://cdn.countryflags.com/thumbs/united-states-of-america/flag-square-250.png'::text
            WHEN (area.name = 'Côte d''Ivoire'::text) THEN 'https://cdn.countryflags.com/thumbs/cote-d-ivoire/flag-square-250.png'::text
            WHEN (area.name = 'Bosnia-Herzegovina'::text) THEN 'https://cdn.countryflags.com/thumbs/bosnia-and-herzegovina/flag-square-250.png'::text
            WHEN (area.name = 'Cape Verde Islands'::text) THEN 'https://cdn.countryflags.com/thumbs/cape-verde/flag-square-250.png'::text
            WHEN (area.name = 'French Guiana'::text) THEN 'https://cdn.countryflags.com/thumbs/france/flag-square-250.png'::text
            WHEN (area.name = 'Congo DR'::text) THEN 'https://cdn.countryflags.com/thumbs/congo-democratic-republic-of-the/flag-square-250.png'::text
            WHEN (area.name = 'Ireland Republic'::text) THEN 'https://cdn.countryflags.com/thumbs/ireland/flag-square-250.png'::text
            WHEN (area.name = 'Macedonia FYR'::text) THEN 'https://cdn.countryflags.com/thumbs/north-macedonia/flag-square-250.png'::text
            ELSE (('https://cdn.countryflags.com/thumbs/'::text || replace(lower(area.name), ' '::text, '-'::text)) || '/flag-square-250.png'::text)
        END AS player_nationality_flag,
    cspp.position_code AS frequent_position,
    cs.competition,
    cs.idcompetition_season,
    ptcsr.mean_rating AS rating
   FROM (((((((scouting.player p
     JOIN scouting.current_season_player_position cspp ON ((p.idplayer = cspp.idplayer)))
     JOIN scouting.team team ON ((p.current_team = team.idteam)))
     JOIN scouting.area area ON ((p.birth_area = area.idareas)))
     JOIN scouting.career_entry ce ON (((p.idplayer = ce.player) AND (p.current_team = ce.team))))
     JOIN scouting.team_competition_season tcs ON ((ce.team_competition_season = tcs.idteam_competition_season)))
     JOIN scouting.current_seasons cs ON ((tcs.competition_season = cs.idcompetition_season)))
     LEFT JOIN player_team_competition_season_rating ptcsr ON (((p.idplayer = ptcsr.player) AND (team.idteam = ptcsr.team) AND (cs.idcompetition_season = ptcsr.competition_season))))
  WHERE (p.status = 'active'::text);


ALTER VIEW scouting.current_players OWNER TO "scoutAdmin";

--
-- TOC entry 221 (class 1259 OID 24971)
-- Name: match_event_carry; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_event_carry (
    idmatch_event integer NOT NULL,
    match integer,
    player integer,
    "matchPeriod" text,
    location_x integer,
    location_y integer,
    minute integer,
    second integer,
    endlocation_x integer,
    endlocation_y integer,
    team integer
);


ALTER TABLE scouting.match_event_carry OWNER TO "scoutAdmin";

--
-- TOC entry 222 (class 1259 OID 24977)
-- Name: match_event_infraction; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_event_infraction (
    idmatch_event integer NOT NULL,
    match integer,
    player integer,
    "matchPeriod" text,
    location_x integer,
    location_y integer,
    minute integer,
    second integer,
    "yellowCard" integer,
    "redCard" integer,
    team integer
);


ALTER TABLE scouting.match_event_infraction OWNER TO "scoutAdmin";

--
-- TOC entry 223 (class 1259 OID 24983)
-- Name: match_event_other; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_event_other (
    idmatch_event integer NOT NULL,
    match integer,
    player integer,
    "matchPeriod" text,
    location_x integer,
    location_y integer,
    minute integer,
    second integer,
    team integer
);


ALTER TABLE scouting.match_event_other OWNER TO "scoutAdmin";

--
-- TOC entry 224 (class 1259 OID 24989)
-- Name: match_event_pass; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_event_pass (
    idmatch_event integer NOT NULL,
    match integer,
    player integer,
    "matchPeriod" text,
    location_x integer,
    location_y integer,
    minute integer,
    second integer,
    accurate integer,
    recipient integer,
    endlocation_x integer,
    endlocation_y integer,
    team integer
);


ALTER TABLE scouting.match_event_pass OWNER TO "scoutAdmin";

--
-- TOC entry 225 (class 1259 OID 24995)
-- Name: match_event_shot; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_event_shot (
    idmatch_event integer NOT NULL,
    match integer,
    player integer,
    "matchPeriod" text,
    location_x integer,
    location_y integer,
    minute integer,
    second integer,
    xg real,
    "postShotXg" real,
    "isGoal" smallint,
    "onTarget" smallint,
    team integer
);


ALTER TABLE scouting.match_event_shot OWNER TO "scoutAdmin";

--
-- TOC entry 226 (class 1259 OID 25001)
-- Name: match_formation_extended; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.match_formation_extended AS
 SELECT mf.match,
    mf.player,
    mf.team,
    mf.assists,
    mf.goals,
    mf."ownGoals",
    mf."redCards",
    mf."yellowCards",
    mf.type,
    mf."shirtNumber",
    mf.competition_season,
    p.short_name AS player_name,
    p.image AS player_image,
    t.icon AS team_logo,
        CASE
            WHEN (mf.team = m.home_team) THEN 'home'::text
            WHEN (mf.team = m.away_team) THEN 'away'::text
            ELSE NULL::text
        END AS side
   FROM (((scouting.match_formation mf
     JOIN scouting.match m ON ((m.idmatch = mf.match)))
     JOIN scouting.player p ON ((p.idplayer = mf.player)))
     JOIN scouting.team t ON ((t.idteam = mf.team)));


ALTER VIEW scouting.match_formation_extended OWNER TO "scoutAdmin";

--
-- TOC entry 229 (class 1259 OID 25016)
-- Name: match_substitution; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_substitution (
    match integer NOT NULL,
    "playerIn" integer NOT NULL,
    "playerOut" integer NOT NULL,
    team integer,
    minute integer,
    "playerInImage" text,
    "playerOutImage" text,
    "teamImage" text
);


ALTER TABLE scouting.match_substitution OWNER TO "scoutAdmin";

--
-- TOC entry 248 (class 1259 OID 49629)
-- Name: match_formation_extended_rating; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.match_formation_extended_rating AS
 SELECT mf.match,
    mf.player,
    mf.team,
    mf.assists,
    mf.goals,
    mf."ownGoals",
    mf."redCards",
    mf."yellowCards",
    mf.type,
    mf."shirtNumber",
    mf.competition_season,
    p.short_name AS player_name,
    p.image AS player_image,
    t.icon AS team_logo,
    pms.rating,
        CASE
            WHEN (mf.team = m.home_team) THEN 'home'::text
            WHEN (mf.team = m.away_team) THEN 'away'::text
            ELSE NULL::text
        END AS side,
        CASE
            WHEN (mf.type = 'lineup'::text) THEN 0
            WHEN (mf.type = 'bench'::text) THEN '-1'::integer
            ELSE ( SELECT ms.minute
               FROM scouting.match_substitution ms
              WHERE ((ms.match = mf.match) AND (ms."playerIn" = mf.player))
             LIMIT 1)
        END AS minute_in,
        CASE
            WHEN (mf.type = 'bench'::text) THEN '-1'::integer
            ELSE COALESCE(( SELECT ms.minute
               FROM scouting.match_substitution ms
              WHERE ((ms.match = mf.match) AND (ms."playerOut" = mf.player))
             LIMIT 1), '-1'::integer)
        END AS minute_out
   FROM ((((scouting.match_formation mf
     JOIN scouting.match m ON ((mf.match = m.idmatch)))
     JOIN scouting.player_match_stats pms ON (((mf.player = pms.player) AND (mf.match = pms.match))))
     JOIN scouting.player p ON ((mf.player = p.idplayer)))
     JOIN scouting.team t ON ((mf.team = t.idteam)));


ALTER VIEW scouting.match_formation_extended_rating OWNER TO "scoutAdmin";

--
-- TOC entry 227 (class 1259 OID 25006)
-- Name: match_goals; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.match_goals (
    match integer NOT NULL,
    scorer integer NOT NULL,
    minute integer NOT NULL,
    second integer NOT NULL,
    assistant integer,
    assist_minute integer,
    assist_second integer,
    team integer
);


ALTER TABLE scouting.match_goals OWNER TO "scoutAdmin";

--
-- TOC entry 246 (class 1259 OID 49605)
-- Name: match_goals_view; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.match_goals_view AS
 SELECT mg.match,
    mg.team,
    mg.scorer,
    mg.minute,
    mg.second,
    mg.assistant,
    mg.assist_minute,
    mg.assist_second,
    p.short_name AS scorer_name,
    p.image AS scorer_image,
    p2.short_name AS assistant_name,
    p2.image AS assistant_image,
    t.icon AS team_logo,
        CASE
            WHEN (mg.team = m.home_team) THEN 'home'::text
            WHEN (mg.team = m.away_team) THEN 'away'::text
            ELSE NULL::text
        END AS side
   FROM ((((scouting.match_goals mg
     JOIN scouting.player p ON ((p.idplayer = mg.scorer)))
     LEFT JOIN scouting.player p2 ON ((p2.idplayer = mg.assistant)))
     JOIN scouting.team t ON ((t.idteam = mg.team)))
     JOIN scouting.match m ON ((m.idmatch = mg.match)));


ALTER VIEW scouting.match_goals_view OWNER TO "scoutAdmin";

--
-- TOC entry 228 (class 1259 OID 25014)
-- Name: match_lineup_match_lineup_id_seq; Type: SEQUENCE; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE scouting.match_lineup ALTER COLUMN match_lineup_id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME scouting.match_lineup_match_lineup_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 230 (class 1259 OID 25022)
-- Name: match_substitution_extended; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.match_substitution_extended AS
 SELECT ms.match,
    ms."playerIn",
    p.short_name AS playerinname,
    ms."playerInImage",
    p1.short_name AS playeroutname,
    ms."playerOutImage",
    ms."playerOut",
    ms.team,
    ms.minute,
    ms."teamImage",
        CASE
            WHEN (ms.team = m.home_team) THEN 'home'::text
            WHEN (ms.team = m.away_team) THEN 'away'::text
            ELSE NULL::text
        END AS side
   FROM (((scouting.match_substitution ms
     JOIN scouting.player p ON ((p.idplayer = ms."playerIn")))
     JOIN scouting.player p1 ON ((p1.idplayer = ms."playerOut")))
     JOIN scouting.match m ON ((m.idmatch = ms.match)));


ALTER VIEW scouting.match_substitution_extended OWNER TO "scoutAdmin";

--
-- TOC entry 231 (class 1259 OID 25027)
-- Name: match_timeline_view; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.match_timeline_view AS
 SELECT mfe.match,
    mfe.player_name AS player1,
    mfe.side AS team,
    mfe."redCards" AS minute,
    NULL::text AS player2,
    'redCard'::text AS type,
        CASE
            WHEN (mfe."redCards" < m."1st_period_end") THEN '1H'::text
            WHEN (mfe."redCards" < m."2nd_period_end") THEN '2H'::text
            WHEN (mfe."redCards" < m.ex_period_end) THEN 'E'::text
            ELSE 'P'::text
        END AS match_period
   FROM (scouting.match_formation_extended mfe
     JOIN scouting.match m ON ((mfe.match = m.idmatch)))
UNION ALL
 SELECT mfe.match,
    mfe.player_name AS player1,
    mfe.side AS team,
    mfe."yellowCards" AS minute,
    NULL::text AS player2,
    'yellowCard'::text AS type,
        CASE
            WHEN (mfe."yellowCards" < m."1st_period_end") THEN '1H'::text
            WHEN (mfe."yellowCards" < m."2nd_period_end") THEN '2H'::text
            WHEN (mfe."yellowCards" < m.ex_period_end) THEN 'E'::text
            ELSE 'P'::text
        END AS match_period
   FROM (scouting.match_formation_extended mfe
     JOIN scouting.match m ON ((mfe.match = m.idmatch)))
UNION ALL
 SELECT mgv.match,
    mgv.scorer_name AS player1,
    mgv.side AS team,
    mgv.minute,
    mgv.assistant_name AS player2,
    'goal'::text AS type,
        CASE
            WHEN (mgv.minute < m."1st_period_end") THEN '1H'::text
            WHEN (mgv.minute < m."2nd_period_end") THEN '2H'::text
            WHEN (mgv.minute < m.ex_period_end) THEN 'E'::text
            ELSE 'P'::text
        END AS match_period
   FROM (scouting.match_goals_view mgv
     JOIN scouting.match m ON ((mgv.match = m.idmatch)))
UNION ALL
 SELECT mse.match,
    mse.playerinname AS player1,
    mse.side AS team,
    mse.minute,
    mse.playeroutname AS player2,
    'substitution'::text AS type,
        CASE
            WHEN (mse.minute < m."1st_period_end") THEN '1H'::text
            WHEN (mse.minute < m."2nd_period_end") THEN '2H'::text
            WHEN (mse.minute < m.ex_period_end) THEN 'E'::text
            ELSE 'P'::text
        END AS match_period
   FROM (scouting.match_substitution_extended mse
     JOIN scouting.match m ON ((mse.match = m.idmatch)));


ALTER VIEW scouting.match_timeline_view OWNER TO "scoutAdmin";

--
-- TOC entry 250 (class 1259 OID 49656)
-- Name: player_match_stats_extended; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.player_match_stats_extended AS
 SELECT pms.idplayer_match_stats,
    pms.match,
    pms.player,
    pms."offensiveDuels",
    pms."progressivePasses",
    pms."forwardPasses",
    pms.crosses,
    pms."keyPasses",
    pms."defensiveDuels",
    pms.interceptions,
    pms.recoveries,
    pms."percent_successfulPasses",
    pms."successfulPasses",
    pms.passes,
    pms."longPasses",
    pms."aerialDuels",
    pms.losses,
    pms."ownHalfLosses",
    pms."opponentHalfRecoveries",
    pms."goalKicks",
    pms."receivedPass",
    pms.dribbles,
    pms."touchInBox",
    pms."position",
    pms.rating,
    m.competition_season
   FROM (scouting.player_match_stats pms
     JOIN scouting.match m ON ((pms.match = m.idmatch)));


ALTER VIEW scouting.player_match_stats_extended OWNER TO "scoutAdmin";

--
-- TOC entry 233 (class 1259 OID 25035)
-- Name: player_match_stats_idplayer_match_stats_seq; Type: SEQUENCE; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE scouting.player_match_stats ALTER COLUMN idplayer_match_stats ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME scouting.player_match_stats_idplayer_match_stats_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 247 (class 1259 OID 49624)
-- Name: player_team_competition_season_rating; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.player_team_competition_season_rating AS
 WITH player_team_competition_season_rating AS (
         SELECT DISTINCT ON (subquery.competition_season, subquery.player, subquery.team) subquery.competition_season,
            subquery.player,
            avg(subquery.rating) OVER (PARTITION BY subquery.player, subquery.competition_season, subquery.team) AS mean_rating,
            subquery.team
           FROM ( SELECT m.competition_season,
                    pms.player,
                    pms.rating,
                    pms.team
                   FROM (scouting.player_match_stats pms
                     JOIN scouting.match m ON ((pms.match = m.idmatch)))
                  WHERE (pms.rating IS NOT NULL)) subquery
        )
 SELECT p.short_name,
    p.image AS player_image,
    ptcsr.competition_season,
    ptcsr.player,
    ptcsr.mean_rating,
    ptcsr.team,
    t.name AS team_name,
    t.icon AS team_image,
    ce."minutesPlayed" AS total_minutes_played,
    ce.appearances AS total_games_played
   FROM ((((player_team_competition_season_rating ptcsr
     JOIN scouting.player p ON ((ptcsr.player = p.idplayer)))
     JOIN scouting.team t ON ((ptcsr.team = t.idteam)))
     JOIN scouting.team_competition_season tcs ON (((ptcsr.competition_season = tcs.competition_season) AND (ptcsr.team = tcs.team))))
     JOIN scouting.career_entry ce ON (((ptcsr.player = ce.player) AND (tcs.idteam_competition_season = ce.team_competition_season))));


ALTER VIEW scouting.player_team_competition_season_rating OWNER TO "scoutAdmin";

--
-- TOC entry 236 (class 1259 OID 25046)
-- Name: team_competition_season_idteam_competition_season_seq; Type: SEQUENCE; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE scouting.team_competition_season ALTER COLUMN idteam_competition_season ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME scouting.team_competition_season_idteam_competition_season_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 237 (class 1259 OID 25048)
-- Name: team_competition_season_round; Type: TABLE; Schema: scouting; Owner: scoutAdmin
--

CREATE TABLE scouting.team_competition_season_round (
    idteam_competition_season_round integer NOT NULL,
    competition_season_round integer NOT NULL,
    team integer NOT NULL,
    group_id integer,
    "totalDraws" integer,
    "totalGoalsAgainst" integer,
    "totalGoalsFor" integer,
    "totalLosses" integer,
    "totalPlayed" integer,
    "totalPoints" integer,
    "totalWins" integer,
    rank integer
);


ALTER TABLE scouting.team_competition_season_round OWNER TO "scoutAdmin";

--
-- TOC entry 238 (class 1259 OID 25051)
-- Name: team_competition_season_round_extended; Type: VIEW; Schema: scouting; Owner: scoutAdmin
--

CREATE VIEW scouting.team_competition_season_round_extended AS
 SELECT tcsr.idteam_competition_season_round,
    tcsr.competition_season_round,
    tcsr.team,
    tcsr.group_id,
    tcsr."totalDraws",
    tcsr."totalGoalsAgainst",
    tcsr."totalGoalsFor",
    tcsr."totalLosses",
    tcsr."totalPlayed",
    tcsr."totalPoints",
    tcsr."totalWins",
    tcsr.rank,
    tcs.idteam_competition_season,
    team_info.icon AS team_icon,
    team_info.city AS team_city,
    team_info.name AS team_name,
    t.area AS team_area_id,
    a.name AS team_area_name,
        CASE
            WHEN (a.name = 'Korea Republic'::text) THEN 'https://cdn.countryflags.com/thumbs/south-korea/flag-square-250.png'::text
            WHEN (a.name = 'United States'::text) THEN 'https://cdn.countryflags.com/thumbs/united-states-of-america/flag-square-250.png'::text
            WHEN (a.name = 'Côte d''Ivoire'::text) THEN 'https://cdn.countryflags.com/thumbs/cote-divoire/flag-square-250.png'::text
            WHEN (a.name = 'Bosnia-Herzegovina'::text) THEN 'https://cdn.countryflags.com/thumbs/bosnia-and-herzegovina/flag-square-250.png'::text
            WHEN (a.name = 'Cape Verde Islands'::text) THEN 'https://cdn.countryflags.com/thumbs/cape-verde/flag-square-250.png'::text
            WHEN (a.name = 'French Guiana'::text) THEN 'https://cdn.countryflags.com/thumbs/france/flag-square-250.png'::text
            WHEN (a.name = 'Congo DR'::text) THEN 'https://cdn.countryflags.com/thumbs/congo-democratic-republic-of-the/flag-square-250.png'::text
            ELSE (('https://cdn.countryflags.com/thumbs/'::text || replace(lower(a.name), ' '::text, '-'::text)) || '/flag-square-250.png'::text)
        END AS team_area_flag,
    sum(COALESCE(
        CASE
            WHEN (tcsr.team = m.home_team) THEN m.home_xg
            ELSE m.away_xg
        END, (0)::real)) AS total_xg,
    sum(COALESCE(
        CASE
            WHEN (tcsr.team = m.home_team) THEN m.away_xg
            ELSE m.home_xg
        END, (0)::real)) AS total_xga,
    (tcsr."totalGoalsFor" - tcsr."totalGoalsAgainst") AS dg
   FROM ((((((scouting.team_competition_season_round tcsr
     JOIN scouting.competition_season_round csr ON ((tcsr.competition_season_round = csr.idcompetition_season_round)))
     JOIN scouting.team_competition_season tcs ON (((csr.competition_season = tcs.competition_season) AND (tcs.team = tcsr.team))))
     LEFT JOIN scouting.match m ON (((m.competition_season = csr.competition_season) AND ((tcsr.team = m.home_team) OR (tcsr.team = m.away_team)))))
     LEFT JOIN scouting.team team_info ON ((tcsr.team = team_info.idteam)))
     JOIN scouting.team t ON ((tcsr.team = t.idteam)))
     JOIN scouting.area a ON ((a.idareas = t.area)))
  GROUP BY tcsr.idteam_competition_season_round, tcs.idteam_competition_season, tcsr.competition_season_round, tcsr.team, tcsr.group_id, tcsr."totalDraws", tcsr."totalGoalsAgainst", tcsr."totalGoalsFor", tcsr."totalLosses", tcsr."totalPlayed", tcsr."totalPoints", tcsr."totalWins", tcsr.rank, team_info.icon, team_info.city, team_info.name, t.area, a.name;


ALTER VIEW scouting.team_competition_season_round_extended OWNER TO "scoutAdmin";

--
-- TOC entry 239 (class 1259 OID 25056)
-- Name: team_competition_season_round_idteam_competition_season_rou_seq; Type: SEQUENCE; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE scouting.team_competition_season_round ALTER COLUMN idteam_competition_season_round ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME scouting.team_competition_season_round_idteam_competition_season_rou_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 3657 (class 2606 OID 25059)
-- Name: area area_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.area
    ADD CONSTRAINT area_pkey PRIMARY KEY (idareas);


--
-- TOC entry 3661 (class 2606 OID 25063)
-- Name: competition competition_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition
    ADD CONSTRAINT competition_pkey PRIMARY KEY (idcompetitions);


--
-- TOC entry 3711 (class 2606 OID 33113)
-- Name: competition_season_assistman competition_season_assistman_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_assistman
    ADD CONSTRAINT competition_season_assistman_pkey PRIMARY KEY (competition_season, player, team);


--
-- TOC entry 3663 (class 2606 OID 25065)
-- Name: competition_season competition_season_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season
    ADD CONSTRAINT competition_season_pkey PRIMARY KEY (idcompetition_season);


--
-- TOC entry 3681 (class 2606 OID 25067)
-- Name: competition_season_round_group competition_season_round_group_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_round_group
    ADD CONSTRAINT competition_season_round_group_pkey PRIMARY KEY (idgroup);


--
-- TOC entry 3679 (class 2606 OID 25069)
-- Name: competition_season_round competition_season_round_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_round
    ADD CONSTRAINT competition_season_round_pkey PRIMARY KEY (idcompetition_season_round);


--
-- TOC entry 3709 (class 2606 OID 33111)
-- Name: competition_season_scorer competition_season_scorer_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_scorer
    ADD CONSTRAINT competition_season_scorer_pkey PRIMARY KEY (competition_season, player, team);


--
-- TOC entry 3683 (class 2606 OID 25071)
-- Name: match_event_carry match_event_carry_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_carry
    ADD CONSTRAINT match_event_carry_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3685 (class 2606 OID 25073)
-- Name: match_event_infraction match_event_infraction_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_infraction
    ADD CONSTRAINT match_event_infraction_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3687 (class 2606 OID 25075)
-- Name: match_event_other match_event_other_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_other
    ADD CONSTRAINT match_event_other_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3689 (class 2606 OID 25077)
-- Name: match_event_pass match_event_pass_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_pass
    ADD CONSTRAINT match_event_pass_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3691 (class 2606 OID 25079)
-- Name: match_event_shot match_event_shot_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_shot
    ADD CONSTRAINT match_event_shot_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3667 (class 2606 OID 25081)
-- Name: match_formation match_formation_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT match_formation_pkey PRIMARY KEY (match, player);


--
-- TOC entry 3693 (class 2606 OID 49611)
-- Name: match_goals match_goals_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_goals
    ADD CONSTRAINT match_goals_pkey PRIMARY KEY (match, scorer, minute, second);


--
-- TOC entry 3669 (class 2606 OID 25085)
-- Name: match_lineup match_lineup_id; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_lineup
    ADD CONSTRAINT match_lineup_id UNIQUE (match_lineup_id);


--
-- TOC entry 3671 (class 2606 OID 25087)
-- Name: match_lineup match_lineup_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_lineup
    ADD CONSTRAINT match_lineup_pkey PRIMARY KEY (match, team, period, second);


--
-- TOC entry 3673 (class 2606 OID 25089)
-- Name: match_lineup_player_position match_lineup_player_position_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_lineup_player_position
    ADD CONSTRAINT match_lineup_player_position_pkey PRIMARY KEY (match_lineup_id, player);


--
-- TOC entry 3665 (class 2606 OID 25091)
-- Name: match match_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT match_pkey PRIMARY KEY (idmatch);


--
-- TOC entry 3695 (class 2606 OID 25093)
-- Name: match_substitution match_substitution_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT match_substitution_pkey PRIMARY KEY (match, "playerIn", "playerOut");


--
-- TOC entry 3659 (class 2606 OID 25061)
-- Name: career_entry pkey_career_entry; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.career_entry
    ADD CONSTRAINT pkey_career_entry PRIMARY KEY (player, team_competition_season);


--
-- TOC entry 3697 (class 2606 OID 25095)
-- Name: player_match_stats player_match; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT player_match UNIQUE (player, match);


--
-- TOC entry 3699 (class 2606 OID 25097)
-- Name: player_match_stats player_match_stats_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT player_match_stats_pkey PRIMARY KEY (idplayer_match_stats);


--
-- TOC entry 3675 (class 2606 OID 25099)
-- Name: player player_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player
    ADD CONSTRAINT player_pkey PRIMARY KEY (idplayer);


--
-- TOC entry 3701 (class 2606 OID 25101)
-- Name: player_positions player_positions_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player_positions
    ADD CONSTRAINT player_positions_pkey PRIMARY KEY (code, player, team_competition_season);


--
-- TOC entry 3703 (class 2606 OID 25103)
-- Name: team_competition_season team_competition_season_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team_competition_season
    ADD CONSTRAINT team_competition_season_pkey PRIMARY KEY (idteam_competition_season);


--
-- TOC entry 3707 (class 2606 OID 25105)
-- Name: team_competition_season_round team_competition_season_round_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team_competition_season_round
    ADD CONSTRAINT team_competition_season_round_pkey PRIMARY KEY (competition_season_round, team);


--
-- TOC entry 3705 (class 2606 OID 25107)
-- Name: team_competition_season team_competition_season_unique; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team_competition_season
    ADD CONSTRAINT team_competition_season_unique UNIQUE (team, competition_season);


--
-- TOC entry 3677 (class 2606 OID 25109)
-- Name: team team_pkey; Type: CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team
    ADD CONSTRAINT team_pkey PRIMARY KEY (idteam);


--
-- TOC entry 3766 (class 2620 OID 25110)
-- Name: match match_update_group_id_trigger; Type: TRIGGER; Schema: scouting; Owner: scoutAdmin
--

CREATE TRIGGER match_update_group_id_trigger BEFORE INSERT OR UPDATE ON scouting.match FOR EACH ROW EXECUTE FUNCTION scouting.match_update_group_id();


--
-- TOC entry 3768 (class 2620 OID 25111)
-- Name: match_substitution on_substitution_insert; Type: TRIGGER; Schema: scouting; Owner: scoutAdmin
--

CREATE TRIGGER on_substitution_insert BEFORE INSERT OR UPDATE ON scouting.match_substitution FOR EACH ROW EXECUTE FUNCTION scouting.on_substitution_insert();


--
-- TOC entry 3769 (class 2620 OID 33173)
-- Name: player_positions update_career_entry_position_trigger; Type: TRIGGER; Schema: scouting; Owner: scoutAdmin
--

CREATE TRIGGER update_career_entry_position_trigger BEFORE INSERT OR UPDATE ON scouting.player_positions FOR EACH ROW EXECUTE FUNCTION scouting.update_career_entry_position();


--
-- TOC entry 3767 (class 2620 OID 25112)
-- Name: match_formation update_match_formation_competition_season; Type: TRIGGER; Schema: scouting; Owner: scoutAdmin
--

CREATE TRIGGER update_match_formation_competition_season BEFORE INSERT OR UPDATE ON scouting.match_formation FOR EACH ROW EXECUTE FUNCTION scouting.update_match_formation_competition_season();


--
-- TOC entry 3714 (class 2606 OID 25113)
-- Name: competition area; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition
    ADD CONSTRAINT area FOREIGN KEY (area) REFERENCES scouting.area(idareas);


--
-- TOC entry 3731 (class 2606 OID 25118)
-- Name: team area; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team
    ADD CONSTRAINT area FOREIGN KEY (area) REFERENCES scouting.area(idareas);


--
-- TOC entry 3716 (class 2606 OID 25123)
-- Name: match away_team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT away_team FOREIGN KEY (away_team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3729 (class 2606 OID 25128)
-- Name: player birth_area; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player
    ADD CONSTRAINT birth_area FOREIGN KEY (birth_area) REFERENCES scouting.area(idareas);


--
-- TOC entry 3715 (class 2606 OID 25133)
-- Name: competition_season competition; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season
    ADD CONSTRAINT competition FOREIGN KEY (competition) REFERENCES scouting.competition(idcompetitions);


--
-- TOC entry 3732 (class 2606 OID 25138)
-- Name: competition_season_round competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_round
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season);


--
-- TOC entry 3755 (class 2606 OID 25143)
-- Name: team_competition_season competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team_competition_season
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season);


--
-- TOC entry 3717 (class 2606 OID 25148)
-- Name: match competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season);


--
-- TOC entry 3721 (class 2606 OID 25153)
-- Name: match_formation competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season) NOT VALID;


--
-- TOC entry 3760 (class 2606 OID 33075)
-- Name: competition_season_scorer competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_scorer
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season);


--
-- TOC entry 3763 (class 2606 OID 33095)
-- Name: competition_season_assistman competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_assistman
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season);


--
-- TOC entry 3733 (class 2606 OID 25158)
-- Name: competition_season_round_group competition_season_round; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_round_group
    ADD CONSTRAINT competition_season_round FOREIGN KEY (competition_season_round) REFERENCES scouting.competition_season_round(idcompetition_season_round);


--
-- TOC entry 3757 (class 2606 OID 25163)
-- Name: team_competition_season_round competition_season_round; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team_competition_season_round
    ADD CONSTRAINT competition_season_round FOREIGN KEY (competition_season_round) REFERENCES scouting.competition_season_round(idcompetition_season_round);


--
-- TOC entry 3718 (class 2606 OID 25168)
-- Name: match group; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT "group" FOREIGN KEY ("group") REFERENCES scouting.competition_season_round_group(idgroup);


--
-- TOC entry 3758 (class 2606 OID 25173)
-- Name: team_competition_season_round group_id; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team_competition_season_round
    ADD CONSTRAINT group_id FOREIGN KEY (group_id) REFERENCES scouting.competition_season_round_group(idgroup);


--
-- TOC entry 3719 (class 2606 OID 25178)
-- Name: match home_team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT home_team FOREIGN KEY (home_team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3734 (class 2606 OID 25183)
-- Name: match_event_carry match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_carry
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3736 (class 2606 OID 25188)
-- Name: match_event_infraction match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_infraction
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3738 (class 2606 OID 25193)
-- Name: match_event_other match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_other
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3740 (class 2606 OID 25198)
-- Name: match_event_pass match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_pass
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3742 (class 2606 OID 25203)
-- Name: match_event_shot match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_shot
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3722 (class 2606 OID 25208)
-- Name: match_formation match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3746 (class 2606 OID 25213)
-- Name: match_substitution match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3725 (class 2606 OID 25218)
-- Name: match_lineup match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_lineup
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3750 (class 2606 OID 25223)
-- Name: player_match_stats match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3744 (class 2606 OID 25228)
-- Name: match_goals match; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_goals
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3727 (class 2606 OID 25233)
-- Name: match_lineup_player_position match_lineup; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_lineup_player_position
    ADD CONSTRAINT match_lineup FOREIGN KEY (match_lineup_id) REFERENCES scouting.match_lineup(match_lineup_id);


--
-- TOC entry 3730 (class 2606 OID 25238)
-- Name: player passport_area; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player
    ADD CONSTRAINT passport_area FOREIGN KEY (passport_area) REFERENCES scouting.area(idareas);


--
-- TOC entry 3712 (class 2606 OID 25243)
-- Name: career_entry player; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.career_entry
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3753 (class 2606 OID 25248)
-- Name: player_positions player; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player_positions
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer) NOT VALID;


--
-- TOC entry 3723 (class 2606 OID 25253)
-- Name: match_formation player; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3728 (class 2606 OID 25258)
-- Name: match_lineup_player_position player; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_lineup_player_position
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3751 (class 2606 OID 25263)
-- Name: player_match_stats player; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3761 (class 2606 OID 33080)
-- Name: competition_season_scorer player; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_scorer
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3764 (class 2606 OID 33100)
-- Name: competition_season_assistman player; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_assistman
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3747 (class 2606 OID 25268)
-- Name: match_substitution playerIn; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT "playerIn" FOREIGN KEY ("playerIn") REFERENCES scouting.player(idplayer);


--
-- TOC entry 3748 (class 2606 OID 25273)
-- Name: match_substitution playerOut; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT "playerOut" FOREIGN KEY ("playerOut") REFERENCES scouting.player(idplayer);


--
-- TOC entry 3720 (class 2606 OID 25278)
-- Name: match round; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT round FOREIGN KEY (round) REFERENCES scouting.competition_season_round(idcompetition_season_round);


--
-- TOC entry 3756 (class 2606 OID 25283)
-- Name: team_competition_season team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team_competition_season
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3759 (class 2606 OID 25288)
-- Name: team_competition_season_round team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.team_competition_season_round
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3724 (class 2606 OID 25293)
-- Name: match_formation team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3749 (class 2606 OID 25298)
-- Name: match_substitution team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3726 (class 2606 OID 25303)
-- Name: match_lineup team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_lineup
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3735 (class 2606 OID 25308)
-- Name: match_event_carry team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_carry
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam) NOT VALID;


--
-- TOC entry 3737 (class 2606 OID 25313)
-- Name: match_event_infraction team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_infraction
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam) NOT VALID;


--
-- TOC entry 3739 (class 2606 OID 25318)
-- Name: match_event_other team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_other
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam) NOT VALID;


--
-- TOC entry 3743 (class 2606 OID 25323)
-- Name: match_event_shot team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_shot
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam) NOT VALID;


--
-- TOC entry 3745 (class 2606 OID 25328)
-- Name: match_goals team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_goals
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam) NOT VALID;


--
-- TOC entry 3741 (class 2606 OID 25333)
-- Name: match_event_pass team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.match_event_pass
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam) NOT VALID;


--
-- TOC entry 3762 (class 2606 OID 33085)
-- Name: competition_season_scorer team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_scorer
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3765 (class 2606 OID 33105)
-- Name: competition_season_assistman team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.competition_season_assistman
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3752 (class 2606 OID 49613)
-- Name: player_match_stats team; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam) NOT VALID;


--
-- TOC entry 3713 (class 2606 OID 25338)
-- Name: career_entry team_competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.career_entry
    ADD CONSTRAINT team_competition_season FOREIGN KEY (team_competition_season) REFERENCES scouting.team_competition_season(idteam_competition_season);


--
-- TOC entry 3754 (class 2606 OID 25343)
-- Name: player_positions team_competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: scoutAdmin
--

ALTER TABLE ONLY scouting.player_positions
    ADD CONSTRAINT team_competition_season FOREIGN KEY (team_competition_season) REFERENCES scouting.team_competition_season(idteam_competition_season);


-- Completed on 2024-01-23 11:06:49

--
-- PostgreSQL database dump complete
--

