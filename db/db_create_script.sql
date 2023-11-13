--
-- PostgreSQL database dump
--

-- Dumped from database version 15.3
-- Dumped by pg_dump version 16.1

-- Started on 2023-11-13 16:23:32

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
-- TOC entry 10 (class 2615 OID 24832)
-- Name: scouting; Type: SCHEMA; Schema: -; Owner: dbadmin
--

CREATE SCHEMA scouting;


ALTER SCHEMA scouting OWNER TO dbadmin;

--
-- TOC entry 253 (class 1255 OID 24833)
-- Name: get_group_id(integer, integer); Type: FUNCTION; Schema: scouting; Owner: dbadmin
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


ALTER FUNCTION scouting.get_group_id(arg_team integer, arg_round integer) OWNER TO dbadmin;

--
-- TOC entry 254 (class 1255 OID 24834)
-- Name: match_update_group_id(); Type: FUNCTION; Schema: scouting; Owner: dbadmin
--

CREATE FUNCTION scouting.match_update_group_id() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.group := scouting.get_group_id(NEW.home_team, NEW.round);
    RETURN NEW;
END;
$$;


ALTER FUNCTION scouting.match_update_group_id() OWNER TO dbadmin;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 223 (class 1259 OID 24835)
-- Name: area; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.area (
    idareas integer NOT NULL,
    name text,
    alpha3code text
);


ALTER TABLE scouting.area OWNER TO dbadmin;

--
-- TOC entry 224 (class 1259 OID 24840)
-- Name: career_entry; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    competition_season integer
);


ALTER TABLE scouting.career_entry OWNER TO dbadmin;

--
-- TOC entry 225 (class 1259 OID 24843)
-- Name: competition; Type: TABLE; Schema: scouting; Owner: dbadmin
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


ALTER TABLE scouting.competition OWNER TO dbadmin;

--
-- TOC entry 226 (class 1259 OID 24848)
-- Name: competition_season; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.competition_season (
    idcompetition_season integer NOT NULL,
    competition integer,
    "startDate" date,
    "endDate" date,
    name text
);


ALTER TABLE scouting.competition_season OWNER TO dbadmin;

--
-- TOC entry 227 (class 1259 OID 24853)
-- Name: competition_season_round; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.competition_season_round (
    idcompetition_season_round integer NOT NULL,
    competition_season integer,
    "startDate" date,
    "endDate" date,
    name text,
    type text
);


ALTER TABLE scouting.competition_season_round OWNER TO dbadmin;

--
-- TOC entry 228 (class 1259 OID 24858)
-- Name: competition_season_round_group; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.competition_season_round_group (
    idgroup integer NOT NULL,
    competition_season_round integer,
    group_name text
);


ALTER TABLE scouting.competition_season_round_group OWNER TO dbadmin;

--
-- TOC entry 229 (class 1259 OID 24863)
-- Name: match; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    away_score_p integer
);


ALTER TABLE scouting.match OWNER TO dbadmin;

--
-- TOC entry 230 (class 1259 OID 24866)
-- Name: match_event_carry; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    endlocation_y integer
);


ALTER TABLE scouting.match_event_carry OWNER TO dbadmin;

--
-- TOC entry 231 (class 1259 OID 24871)
-- Name: match_event_infraction; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    "redCard" integer
);


ALTER TABLE scouting.match_event_infraction OWNER TO dbadmin;

--
-- TOC entry 232 (class 1259 OID 24876)
-- Name: match_event_other; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.match_event_other (
    idmatch_event integer NOT NULL,
    match integer,
    player integer,
    "matchPeriod" text,
    location_x integer,
    location_y integer,
    minute integer,
    second integer
);


ALTER TABLE scouting.match_event_other OWNER TO dbadmin;

--
-- TOC entry 233 (class 1259 OID 24881)
-- Name: match_event_pass; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    endlocation_y integer
);


ALTER TABLE scouting.match_event_pass OWNER TO dbadmin;

--
-- TOC entry 234 (class 1259 OID 24886)
-- Name: match_event_shot; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    "onTarget" smallint
);


ALTER TABLE scouting.match_event_shot OWNER TO dbadmin;

--
-- TOC entry 235 (class 1259 OID 24891)
-- Name: match_formation; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    "shirtNumber" integer
);


ALTER TABLE scouting.match_formation OWNER TO dbadmin;

--
-- TOC entry 236 (class 1259 OID 24896)
-- Name: match_lineup; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.match_lineup (
    match integer NOT NULL,
    team integer NOT NULL,
    period text NOT NULL,
    match_lineup_id integer NOT NULL,
    lineup text,
    second integer NOT NULL
);


ALTER TABLE scouting.match_lineup OWNER TO dbadmin;

--
-- TOC entry 237 (class 1259 OID 24901)
-- Name: match_lineup_match_lineup_id_seq; Type: SEQUENCE; Schema: scouting; Owner: dbadmin
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
-- TOC entry 238 (class 1259 OID 24902)
-- Name: match_lineup_player_position; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.match_lineup_player_position (
    match_lineup_id integer NOT NULL,
    player integer NOT NULL,
    "position" text NOT NULL
);


ALTER TABLE scouting.match_lineup_player_position OWNER TO dbadmin;

--
-- TOC entry 239 (class 1259 OID 24907)
-- Name: match_substitution; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.match_substitution (
    match integer NOT NULL,
    "playerIn" integer NOT NULL,
    "playerOut" integer NOT NULL,
    team integer,
    minute integer
);


ALTER TABLE scouting.match_substitution OWNER TO dbadmin;

--
-- TOC entry 240 (class 1259 OID 24911)
-- Name: player; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    tm_market_value bit(1),
    currency text
);


ALTER TABLE scouting.player OWNER TO dbadmin;

--
-- TOC entry 241 (class 1259 OID 24916)
-- Name: player_match_stats; Type: TABLE; Schema: scouting; Owner: dbadmin
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
    "successfulPasses" real,
    "longPasses" integer,
    "aerialDuels" integer,
    losses integer,
    "ownHalfLosses" integer,
    "opponentHalfRecoveries" integer,
    "goalKicks" integer,
    "receivedPass" integer,
    dribbles integer,
    "touchInBox" integer
);


ALTER TABLE scouting.player_match_stats OWNER TO dbadmin;

--
-- TOC entry 242 (class 1259 OID 24919)
-- Name: player_match_stats_idplayer_match_stats_seq; Type: SEQUENCE; Schema: scouting; Owner: dbadmin
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
-- TOC entry 243 (class 1259 OID 24920)
-- Name: player_positions; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.player_positions (
    percent integer,
    code text NOT NULL,
    name text,
    team_competition_season integer NOT NULL,
    player integer NOT NULL
);


ALTER TABLE scouting.player_positions OWNER TO dbadmin;

--
-- TOC entry 244 (class 1259 OID 24925)
-- Name: team; Type: TABLE; Schema: scouting; Owner: dbadmin
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


ALTER TABLE scouting.team OWNER TO dbadmin;

--
-- TOC entry 245 (class 1259 OID 24930)
-- Name: team_competition_season; Type: TABLE; Schema: scouting; Owner: dbadmin
--

CREATE TABLE scouting.team_competition_season (
    idteam_competition_season integer NOT NULL,
    team integer,
    competition_season integer
);


ALTER TABLE scouting.team_competition_season OWNER TO dbadmin;

--
-- TOC entry 246 (class 1259 OID 24933)
-- Name: team_competition_season_idteam_competition_season_seq; Type: SEQUENCE; Schema: scouting; Owner: dbadmin
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
-- TOC entry 247 (class 1259 OID 24934)
-- Name: team_competition_season_round; Type: TABLE; Schema: scouting; Owner: dbadmin
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


ALTER TABLE scouting.team_competition_season_round OWNER TO dbadmin;

--
-- TOC entry 248 (class 1259 OID 24937)
-- Name: team_competition_season_round_idteam_competition_season_rou_seq; Type: SEQUENCE; Schema: scouting; Owner: dbadmin
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
-- TOC entry 3887 (class 2606 OID 24939)
-- Name: area area_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.area
    ADD CONSTRAINT area_pkey PRIMARY KEY (idareas);


--
-- TOC entry 3889 (class 2606 OID 24941)
-- Name: career_entry career_entry_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.career_entry
    ADD CONSTRAINT career_entry_pkey PRIMARY KEY (player, team_competition_season);


--
-- TOC entry 3891 (class 2606 OID 24943)
-- Name: competition competition_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.competition
    ADD CONSTRAINT competition_pkey PRIMARY KEY (idcompetitions);


--
-- TOC entry 3893 (class 2606 OID 24945)
-- Name: competition_season competition_season_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.competition_season
    ADD CONSTRAINT competition_season_pkey PRIMARY KEY (idcompetition_season);


--
-- TOC entry 3897 (class 2606 OID 24947)
-- Name: competition_season_round_group competition_season_round_group_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.competition_season_round_group
    ADD CONSTRAINT competition_season_round_group_pkey PRIMARY KEY (idgroup);


--
-- TOC entry 3895 (class 2606 OID 24949)
-- Name: competition_season_round competition_season_round_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.competition_season_round
    ADD CONSTRAINT competition_season_round_pkey PRIMARY KEY (idcompetition_season_round);


--
-- TOC entry 3901 (class 2606 OID 24951)
-- Name: match_event_carry match_event_carry_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_carry
    ADD CONSTRAINT match_event_carry_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3903 (class 2606 OID 24953)
-- Name: match_event_infraction match_event_infraction_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_infraction
    ADD CONSTRAINT match_event_infraction_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3905 (class 2606 OID 24955)
-- Name: match_event_other match_event_other_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_other
    ADD CONSTRAINT match_event_other_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3907 (class 2606 OID 24957)
-- Name: match_event_pass match_event_pass_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_pass
    ADD CONSTRAINT match_event_pass_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3909 (class 2606 OID 24959)
-- Name: match_event_shot match_event_shot_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_shot
    ADD CONSTRAINT match_event_shot_pkey PRIMARY KEY (idmatch_event);


--
-- TOC entry 3911 (class 2606 OID 24961)
-- Name: match_formation match_formation_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT match_formation_pkey PRIMARY KEY (match, player);


--
-- TOC entry 3913 (class 2606 OID 24965)
-- Name: match_lineup match_lineup_id; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_lineup
    ADD CONSTRAINT match_lineup_id UNIQUE (match_lineup_id);


--
-- TOC entry 3915 (class 2606 OID 32792)
-- Name: match_lineup match_lineup_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_lineup
    ADD CONSTRAINT match_lineup_pkey PRIMARY KEY (match, team, period, second);


--
-- TOC entry 3917 (class 2606 OID 32796)
-- Name: match_lineup_player_position match_lineup_player_position_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_lineup_player_position
    ADD CONSTRAINT match_lineup_player_position_pkey PRIMARY KEY (match_lineup_id, player);


--
-- TOC entry 3899 (class 2606 OID 24969)
-- Name: match match_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT match_pkey PRIMARY KEY (idmatch);


--
-- TOC entry 3919 (class 2606 OID 24971)
-- Name: match_substitution match_substitution_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT match_substitution_pkey PRIMARY KEY (match, "playerIn", "playerOut");


--
-- TOC entry 3923 (class 2606 OID 32776)
-- Name: player_match_stats player_match; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT player_match UNIQUE (player, match);


--
-- TOC entry 3925 (class 2606 OID 24973)
-- Name: player_match_stats player_match_stats_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT player_match_stats_pkey PRIMARY KEY (idplayer_match_stats);


--
-- TOC entry 3921 (class 2606 OID 24975)
-- Name: player player_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player
    ADD CONSTRAINT player_pkey PRIMARY KEY (idplayer);


--
-- TOC entry 3927 (class 2606 OID 24977)
-- Name: player_positions player_positions_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player_positions
    ADD CONSTRAINT player_positions_pkey PRIMARY KEY (code, player, team_competition_season);


--
-- TOC entry 3931 (class 2606 OID 24979)
-- Name: team_competition_season team_competition_season_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team_competition_season
    ADD CONSTRAINT team_competition_season_pkey PRIMARY KEY (idteam_competition_season);


--
-- TOC entry 3935 (class 2606 OID 32772)
-- Name: team_competition_season_round team_competition_season_round_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team_competition_season_round
    ADD CONSTRAINT team_competition_season_round_pkey PRIMARY KEY (competition_season_round, team);


--
-- TOC entry 3933 (class 2606 OID 32784)
-- Name: team_competition_season team_competition_season_unique; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team_competition_season
    ADD CONSTRAINT team_competition_season_unique UNIQUE (team, competition_season);


--
-- TOC entry 3929 (class 2606 OID 24983)
-- Name: team team_pkey; Type: CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team
    ADD CONSTRAINT team_pkey PRIMARY KEY (idteam);


--
-- TOC entry 3975 (class 2620 OID 24984)
-- Name: match match_update_group_id_trigger; Type: TRIGGER; Schema: scouting; Owner: dbadmin
--

CREATE TRIGGER match_update_group_id_trigger BEFORE INSERT OR UPDATE ON scouting.match FOR EACH ROW EXECUTE FUNCTION scouting.match_update_group_id();


--
-- TOC entry 3938 (class 2606 OID 24985)
-- Name: competition area; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.competition
    ADD CONSTRAINT area FOREIGN KEY (area) REFERENCES scouting.area(idareas);


--
-- TOC entry 3969 (class 2606 OID 24990)
-- Name: team area; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team
    ADD CONSTRAINT area FOREIGN KEY (area) REFERENCES scouting.area(idareas);


--
-- TOC entry 3942 (class 2606 OID 24995)
-- Name: match away_team; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT away_team FOREIGN KEY (away_team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3963 (class 2606 OID 25000)
-- Name: player birth_area; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player
    ADD CONSTRAINT birth_area FOREIGN KEY (birth_area) REFERENCES scouting.area(idareas);


--
-- TOC entry 3939 (class 2606 OID 25005)
-- Name: competition_season competition; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.competition_season
    ADD CONSTRAINT competition FOREIGN KEY (competition) REFERENCES scouting.competition(idcompetitions);


--
-- TOC entry 3940 (class 2606 OID 25010)
-- Name: competition_season_round competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.competition_season_round
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season);


--
-- TOC entry 3970 (class 2606 OID 25015)
-- Name: team_competition_season competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team_competition_season
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season);


--
-- TOC entry 3943 (class 2606 OID 25020)
-- Name: match competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT competition_season FOREIGN KEY (competition_season) REFERENCES scouting.competition_season(idcompetition_season);


--
-- TOC entry 3941 (class 2606 OID 25025)
-- Name: competition_season_round_group competition_season_round; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.competition_season_round_group
    ADD CONSTRAINT competition_season_round FOREIGN KEY (competition_season_round) REFERENCES scouting.competition_season_round(idcompetition_season_round);


--
-- TOC entry 3972 (class 2606 OID 25030)
-- Name: team_competition_season_round competition_season_round; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team_competition_season_round
    ADD CONSTRAINT competition_season_round FOREIGN KEY (competition_season_round) REFERENCES scouting.competition_season_round(idcompetition_season_round);


--
-- TOC entry 3944 (class 2606 OID 25035)
-- Name: match group; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT "group" FOREIGN KEY ("group") REFERENCES scouting.competition_season_round_group(idgroup);


--
-- TOC entry 3973 (class 2606 OID 25040)
-- Name: team_competition_season_round group_id; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team_competition_season_round
    ADD CONSTRAINT group_id FOREIGN KEY (group_id) REFERENCES scouting.competition_season_round_group(idgroup);


--
-- TOC entry 3945 (class 2606 OID 25045)
-- Name: match home_team; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT home_team FOREIGN KEY (home_team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3947 (class 2606 OID 25050)
-- Name: match_event_carry match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_carry
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3948 (class 2606 OID 25055)
-- Name: match_event_infraction match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_infraction
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3949 (class 2606 OID 25060)
-- Name: match_event_other match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_other
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3950 (class 2606 OID 25065)
-- Name: match_event_pass match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_pass
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3951 (class 2606 OID 25070)
-- Name: match_event_shot match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_event_shot
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3952 (class 2606 OID 25075)
-- Name: match_formation match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3959 (class 2606 OID 25080)
-- Name: match_substitution match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3955 (class 2606 OID 25085)
-- Name: match_lineup match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_lineup
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3965 (class 2606 OID 25090)
-- Name: player_match_stats match; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT match FOREIGN KEY (match) REFERENCES scouting.match(idmatch);


--
-- TOC entry 3957 (class 2606 OID 25095)
-- Name: match_lineup_player_position match_lineup; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_lineup_player_position
    ADD CONSTRAINT match_lineup FOREIGN KEY (match_lineup_id) REFERENCES scouting.match_lineup(match_lineup_id);


--
-- TOC entry 3964 (class 2606 OID 25100)
-- Name: player passport_area; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player
    ADD CONSTRAINT passport_area FOREIGN KEY (passport_area) REFERENCES scouting.area(idareas);


--
-- TOC entry 3936 (class 2606 OID 25105)
-- Name: career_entry player; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.career_entry
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3967 (class 2606 OID 25110)
-- Name: player_positions player; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player_positions
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer) NOT VALID;


--
-- TOC entry 3953 (class 2606 OID 25115)
-- Name: match_formation player; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3958 (class 2606 OID 25120)
-- Name: match_lineup_player_position player; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_lineup_player_position
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3966 (class 2606 OID 25125)
-- Name: player_match_stats player; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player_match_stats
    ADD CONSTRAINT player FOREIGN KEY (player) REFERENCES scouting.player(idplayer);


--
-- TOC entry 3960 (class 2606 OID 25130)
-- Name: match_substitution playerIn; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT "playerIn" FOREIGN KEY ("playerIn") REFERENCES scouting.player(idplayer);


--
-- TOC entry 3961 (class 2606 OID 25135)
-- Name: match_substitution playerOut; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT "playerOut" FOREIGN KEY ("playerOut") REFERENCES scouting.player(idplayer);


--
-- TOC entry 3946 (class 2606 OID 25140)
-- Name: match round; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match
    ADD CONSTRAINT round FOREIGN KEY (round) REFERENCES scouting.competition_season_round(idcompetition_season_round);


--
-- TOC entry 3971 (class 2606 OID 25145)
-- Name: team_competition_season team; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team_competition_season
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3974 (class 2606 OID 25150)
-- Name: team_competition_season_round team; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.team_competition_season_round
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3954 (class 2606 OID 25155)
-- Name: match_formation team; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_formation
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3962 (class 2606 OID 25160)
-- Name: match_substitution team; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_substitution
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3956 (class 2606 OID 25165)
-- Name: match_lineup team; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.match_lineup
    ADD CONSTRAINT team FOREIGN KEY (team) REFERENCES scouting.team(idteam);


--
-- TOC entry 3937 (class 2606 OID 25170)
-- Name: career_entry team_competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.career_entry
    ADD CONSTRAINT team_competition_season FOREIGN KEY (team_competition_season) REFERENCES scouting.team_competition_season(idteam_competition_season);


--
-- TOC entry 3968 (class 2606 OID 25175)
-- Name: player_positions team_competition_season; Type: FK CONSTRAINT; Schema: scouting; Owner: dbadmin
--

ALTER TABLE ONLY scouting.player_positions
    ADD CONSTRAINT team_competition_season FOREIGN KEY (team_competition_season) REFERENCES scouting.team_competition_season(idteam_competition_season);


-- Completed on 2023-11-13 16:23:36

--
-- PostgreSQL database dump complete
--

