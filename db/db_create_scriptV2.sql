-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
-- -----------------------------------------------------
-- Schema scouting
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema scouting
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `scouting` DEFAULT CHARACTER SET utf8mb3 ;
USE `scouting` ;

-- -----------------------------------------------------
-- Table `scouting`.`area`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`area` (
  `idareas` INT NOT NULL,
  `alpha3code` VARCHAR(45) NULL DEFAULT NULL,
  `name` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`idareas`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`player`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`player` (
  `idplayer` INT NOT NULL,
  `name` VARCHAR(100) NULL DEFAULT NULL,
  `short_name` VARCHAR(45) NULL DEFAULT NULL,
  `birth_area` INT NULL DEFAULT NULL,
  `birth_date` DATE NULL DEFAULT NULL,
  `image` VARCHAR(200) NULL DEFAULT NULL,
  `foot` VARCHAR(45) NULL DEFAULT NULL,
  `height` INT NULL DEFAULT NULL,
  `weight` INT NULL DEFAULT NULL,
  `status` VARCHAR(45) NULL DEFAULT NULL,
  `gender` VARCHAR(45) NULL DEFAULT NULL,
  `role_code2` VARCHAR(45) NULL DEFAULT NULL,
  `role_code3` VARCHAR(45) NULL DEFAULT NULL,
  `role_name` VARCHAR(45) NULL DEFAULT NULL,
  `market_value` INT NULL DEFAULT NULL,
  `contract_expiration` DATE NULL DEFAULT NULL,
  `contract_agency` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`idplayer`),
  INDEX `birth_area_idx` (`birth_area` ASC) VISIBLE,
  CONSTRAINT `birth_area`
    FOREIGN KEY (`birth_area`)
    REFERENCES `scouting`.`area` (`idareas`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`competition`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`competition` (
  `idcompetitions` INT NOT NULL,
  `name` VARCHAR(45) NULL DEFAULT NULL,
  `area` INT NULL DEFAULT NULL,
  `gender` VARCHAR(45) NULL DEFAULT NULL,
  `type` VARCHAR(45) NULL DEFAULT NULL,
  `format` VARCHAR(45) NULL DEFAULT NULL,
  `divisionLevel` INT NULL DEFAULT NULL,
  `category` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`idcompetitions`),
  INDEX `area_idx` (`area` ASC) VISIBLE,
  CONSTRAINT `area`
    FOREIGN KEY (`area`)
    REFERENCES `scouting`.`area` (`idareas`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`competition_season`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`competition_season` (
  `idcompetition_season` INT NOT NULL AUTO_INCREMENT,
  `startDate` DATE NULL DEFAULT NULL,
  `endDate` DATE NULL DEFAULT NULL,
  `name` VARCHAR(45) NULL DEFAULT NULL,
  `competition` INT NOT NULL,
  `icon` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`idcompetition_season`, `competition`),
  INDEX `competition_idx` (`competition` ASC) VISIBLE,
  CONSTRAINT `competition`
    FOREIGN KEY (`competition`)
    REFERENCES `scouting`.`competition` (`idcompetitions`))
ENGINE = InnoDB
AUTO_INCREMENT = 189054
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`team`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`team` (
  `idteam` INT NOT NULL,
  `name` VARCHAR(45) NULL DEFAULT NULL,
  `official_name` VARCHAR(45) NULL DEFAULT NULL,
  `icon` VARCHAR(200) NULL DEFAULT NULL,
  `gender` VARCHAR(45) NULL DEFAULT NULL,
  `type` VARCHAR(45) NULL DEFAULT NULL,
  `city` VARCHAR(45) NULL DEFAULT NULL,
  `category` VARCHAR(45) NULL DEFAULT NULL,
  `area` INT NULL DEFAULT NULL,
  PRIMARY KEY (`idteam`),
  INDEX `area_idx` (`area` ASC) VISIBLE,
  CONSTRAINT `area_team`
    FOREIGN KEY (`area`)
    REFERENCES `scouting`.`area` (`idareas`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`team_competition_season`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`team_competition_season` (
  `idteam_competition_season` INT NOT NULL AUTO_INCREMENT,
  `competition_season` INT NOT NULL,
  `team` INT NOT NULL,
  `totalDraws` INT NULL DEFAULT NULL,
  `totalGoalsAgainst` INT NULL DEFAULT NULL,
  `totalGoalsFor` INT NULL DEFAULT NULL,
  `totalLosses` INT NULL DEFAULT NULL,
  `totalPlayed` INT NULL DEFAULT NULL,
  `totalPoints` INT NULL DEFAULT NULL,
  `totalWins` INT NULL DEFAULT NULL,
  PRIMARY KEY (`team`, `competition_season`),
  UNIQUE INDEX `idteam_competition_season_UNIQUE` (`idteam_competition_season` ASC) VISIBLE,
  INDEX `team_idx` (`team` ASC) VISIBLE,
  INDEX `competition_season_idx` (`competition_season` ASC) VISIBLE,
  INDEX `team_idx1` (`idteam_competition_season` ASC) VISIBLE,
  CONSTRAINT `tmc_competition_season_fk`
    FOREIGN KEY (`competition_season`)
    REFERENCES `scouting`.`competition_season` (`idcompetition_season`),
  CONSTRAINT `tmc_team_fk`
    FOREIGN KEY (`team`)
    REFERENCES `scouting`.`team` (`idteam`))
ENGINE = InnoDB
AUTO_INCREMENT = 1748
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`career_entry`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`career_entry` (
  `player` INT NOT NULL,
  `team_competition_season` INT NOT NULL,
  `appearances` INT NULL DEFAULT NULL,
  `goal` INT NULL DEFAULT NULL,
  `minutesPlayed` INT NULL DEFAULT NULL,
  `penalties` INT NULL DEFAULT NULL,
  `redCards` INT NULL DEFAULT NULL,
  `shirtNumber` INT NULL DEFAULT NULL,
  `substituteIn` INT NULL DEFAULT NULL,
  `substituteOnBench` INT NULL DEFAULT NULL,
  `substituteOut` INT NULL DEFAULT NULL,
  `yellowCard` INT NULL DEFAULT NULL,
  PRIMARY KEY (`player`, `team_competition_season`),
  INDEX `team_competition_season_fk_idx` (`team_competition_season` ASC) VISIBLE,
  INDEX `team_competition_season_2fk_idx` (`team_competition_season` ASC) VISIBLE,
  INDEX `carrer_team_competition_season_fk_idx` (`team_competition_season` ASC) VISIBLE,
  CONSTRAINT `carrer_player_fk`
    FOREIGN KEY (`player`)
    REFERENCES `scouting`.`player` (`idplayer`),
  CONSTRAINT `carrer_team_competition_season_fk`
    FOREIGN KEY (`team_competition_season`)
    REFERENCES `scouting`.`team_competition_season` (`idteam_competition_season`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`match`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match` (
  `idmatch` INT NOT NULL,
  `competition_season` INT NULL DEFAULT NULL,
  `home_team` INT NULL DEFAULT NULL,
  `away_team` INT NULL DEFAULT NULL,
  `date` DATETIME NULL DEFAULT NULL,
  `home_score` INT NULL DEFAULT NULL,
  `away_score` INT NULL DEFAULT NULL,
  `winner` INT NULL DEFAULT NULL,
  PRIMARY KEY (`idmatch`),
  INDEX `competition_season_idx` (`competition_season` ASC) VISIBLE,
  INDEX `home_team_idx` (`home_team` ASC) VISIBLE,
  INDEX `away_team_idx` (`away_team` ASC) VISIBLE,
  CONSTRAINT `away_team`
    FOREIGN KEY (`away_team`)
    REFERENCES `scouting`.`team` (`idteam`),
  CONSTRAINT `home_team`
    FOREIGN KEY (`home_team`)
    REFERENCES `scouting`.`team` (`idteam`),
  CONSTRAINT `match_competition_season_fk`
    FOREIGN KEY (`competition_season`)
    REFERENCES `scouting`.`competition_season` (`idcompetition_season`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`match_event_other`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_event_other` (
  `idmatch_event` INT NOT NULL,
  `match` INT NOT NULL,
  `player` INT NULL DEFAULT NULL,
  `matchPeriod` VARCHAR(45) NULL DEFAULT NULL,
  `location_x` INT NULL DEFAULT NULL,
  `location_y` INT NULL DEFAULT NULL,
  `minute` INT NULL DEFAULT NULL,
  `second` INT NULL DEFAULT NULL,
  PRIMARY KEY (`idmatch_event`),
  INDEX `match_idx` (`match` ASC) VISIBLE,
  CONSTRAINT `meo_match_fk`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`match_formation`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_formation` (
  `match` INT NOT NULL,
  `player` INT NOT NULL,
  `team` INT NOT NULL,
  `assists` INT NULL DEFAULT NULL,
  `goals` INT NULL DEFAULT NULL,
  `ownGoals` INT NULL DEFAULT NULL,
  `redCards` INT NULL DEFAULT NULL,
  `shirtNumber` INT NULL DEFAULT NULL,
  `yellowCards` INT NULL DEFAULT NULL,
  `minute` INT NULL DEFAULT NULL,
  `type` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`match`, `player`),
  INDEX `player_idx` (`player` ASC) VISIBLE,
  INDEX `team_idx` (`team` ASC) VISIBLE,
  CONSTRAINT `match_fk`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`),
  CONSTRAINT `player_fk`
    FOREIGN KEY (`player`)
    REFERENCES `scouting`.`player` (`idplayer`),
  CONSTRAINT `team_fk`
    FOREIGN KEY (`team`)
    REFERENCES `scouting`.`team` (`idteam`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`match_lineup`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_lineup` (
  `match` INT NOT NULL,
  `team` INT NOT NULL,
  `period` VARCHAR(45) NOT NULL,
  `second` INT NOT NULL,
  `match_lineup_id` INT NOT NULL AUTO_INCREMENT,
  `lineup` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`match`, `team`, `period`, `second`),
  UNIQUE INDEX `id_UNIQUE` (`match_lineup_id` ASC) VISIBLE,
  INDEX `team_idx` (`team` ASC) VISIBLE,
  CONSTRAINT `ml_match_fk`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`),
  CONSTRAINT `ml_team_fk`
    FOREIGN KEY (`team`)
    REFERENCES `scouting`.`team` (`idteam`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`match_lineup_player_position`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_lineup_player_position` (
  `match_lineup_id` INT NOT NULL,
  `player` INT NOT NULL,
  `position` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`match_lineup_id`, `player`, `position`),
  INDEX `mlpp_player_fk_idx` (`player` ASC) VISIBLE,
  CONSTRAINT `match_lineup_id`
    FOREIGN KEY (`match_lineup_id`)
    REFERENCES `scouting`.`match_lineup` (`match_lineup_id`),
  CONSTRAINT `mlpp_player_fk`
    FOREIGN KEY (`player`)
    REFERENCES `scouting`.`player` (`idplayer`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`match_substitution`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_substitution` (
  `match` INT NOT NULL,
  `playerIn` INT NOT NULL,
  `playerOut` INT NOT NULL,
  `team` INT NULL DEFAULT NULL,
  `minute` INT NULL DEFAULT NULL,
  PRIMARY KEY (`match`, `playerIn`, `playerOut`),
  INDEX `playerIn_idx` (`playerIn` ASC) VISIBLE,
  INDEX `playerOut_idx` (`playerOut` ASC) VISIBLE,
  INDEX `team_idx` (`team` ASC) VISIBLE,
  CONSTRAINT `ms_match_fk`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`),
  CONSTRAINT `ms_team_fk`
    FOREIGN KEY (`team`)
    REFERENCES `scouting`.`team` (`idteam`),
  CONSTRAINT `playerIn_fk`
    FOREIGN KEY (`playerIn`)
    REFERENCES `scouting`.`player` (`idplayer`),
  CONSTRAINT `playerOut_fk`
    FOREIGN KEY (`playerOut`)
    REFERENCES `scouting`.`player` (`idplayer`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`player_match_stats`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`player_match_stats` (
  `idplayer_match_stats` INT NOT NULL AUTO_INCREMENT,
  `match` INT NULL DEFAULT NULL,
  `player` INT NULL DEFAULT NULL,
  `offensiveDuels` INT NULL DEFAULT NULL,
  `progressivePasses` INT NULL DEFAULT NULL,
  `forwardPasses` INT NULL DEFAULT NULL,
  `crosses` INT NULL DEFAULT NULL,
  `keyPasses` INT NULL DEFAULT NULL,
  `defensiveDuels` INT NULL DEFAULT NULL,
  `interceptions` INT NULL DEFAULT NULL,
  `recoveries` INT NULL DEFAULT NULL,
  `successfulPasses` FLOAT NULL DEFAULT NULL,
  `longPasses` INT NULL DEFAULT NULL,
  `aerialDuels` INT NULL DEFAULT NULL,
  `losses` INT NULL DEFAULT NULL,
  `ownHalfLosses` INT NULL DEFAULT NULL,
  `opponentHalfRecoveries` INT NULL DEFAULT NULL,
  `goalKicks` INT NULL DEFAULT NULL,
  `receivedPass` INT NULL DEFAULT NULL,
  `dribbles` INT NULL DEFAULT NULL,
  `touchInBox` INT NULL DEFAULT NULL,
  PRIMARY KEY (`idplayer_match_stats`),
  INDEX `match_idx` (`match` ASC) VISIBLE,
  INDEX `player_idx` (`player` ASC) VISIBLE,
  CONSTRAINT `pms_match`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`),
  CONSTRAINT `pms_player_fk`
    FOREIGN KEY (`player`)
    REFERENCES `scouting`.`player` (`idplayer`))
ENGINE = InnoDB
AUTO_INCREMENT = 54958
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`player_positions`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`player_positions` (
  `player` INT NOT NULL,
  `percent` INT NULL DEFAULT NULL,
  `code` VARCHAR(45) NOT NULL,
  `name` VARCHAR(45) NULL DEFAULT NULL,
  `team_competition_season` INT NOT NULL,
  PRIMARY KEY (`code`, `team_competition_season`, `player`),
  INDEX `player_idx` (`player` ASC) VISIBLE,
  INDEX `tam_competition_season_fk_idx` (`team_competition_season` ASC) VISIBLE,
  CONSTRAINT `pp_player_fk`
    FOREIGN KEY (`player`)
    REFERENCES `scouting`.`player` (`idplayer`),
  CONSTRAINT `pp_team_competition_season_fk`
    FOREIGN KEY (`team_competition_season`)
    REFERENCES `scouting`.`team_competition_season` (`idteam_competition_season`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb4
COLLATE = utf8mb4_0900_ai_ci;


-- -----------------------------------------------------
-- Table `scouting`.`round`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`round` (
  `competition_season` INT NOT NULL,
  `startDate` DATE NOT NULL,
  `endDate` DATE NOT NULL,
  `name` VARCHAR(45) NULL DEFAULT NULL,
  PRIMARY KEY (`competition_season`, `startDate`, `endDate`),
  CONSTRAINT `round_competition_season_fk`
    FOREIGN KEY (`competition_season`)
    REFERENCES `scouting`.`competition_season` (`idcompetition_season`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`match_event_shot`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_event_shot` (
  `idmatch_event` INT NOT NULL,
  `match` INT NOT NULL,
  `player` INT NULL DEFAULT NULL,
  `matchPeriod` VARCHAR(45) NULL DEFAULT NULL,
  `location_x` INT NULL DEFAULT NULL,
  `location_y` INT NULL DEFAULT NULL,
  `minute` INT NULL DEFAULT NULL,
  `second` INT NULL DEFAULT NULL,
  `isGoal` TINYINT NULL DEFAULT NULL,
  `onTarget` TINYINT NULL DEFAULT NULL,
  `xg` FLOAT NULL DEFAULT NULL,
  `postShotXg` FLOAT NULL DEFAULT NULL,
  PRIMARY KEY (`idmatch_event`),
  INDEX `match_idx` (`match` ASC) VISIBLE,
  CONSTRAINT `mes_match_fk`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`match_event_pass`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_event_pass` (
  `idmatch_event` INT NOT NULL,
  `match` INT NOT NULL,
  `player` INT NULL DEFAULT NULL,
  `matchPeriod` VARCHAR(45) NULL DEFAULT NULL,
  `location_x` INT NULL DEFAULT NULL,
  `location_y` INT NULL DEFAULT NULL,
  `minute` INT NULL DEFAULT NULL,
  `second` INT NULL DEFAULT NULL,
  `accurate` TINYINT NULL DEFAULT NULL,
  `recipient` INT NULL DEFAULT NULL,
  `endlocation_x` INT NULL DEFAULT NULL,
  `endlocation_y` INT NULL DEFAULT NULL,
  PRIMARY KEY (`idmatch_event`),
  INDEX `match_idx` (`match` ASC) VISIBLE,
  CONSTRAINT `mep_match_fk`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`match_event_carry`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_event_carry` (
  `idmatch_event` INT NOT NULL,
  `match` INT NOT NULL,
  `player` INT NULL DEFAULT NULL,
  `matchPeriod` VARCHAR(45) NULL DEFAULT NULL,
  `location_x` INT NULL DEFAULT NULL,
  `location_y` INT NULL DEFAULT NULL,
  `minute` INT NULL DEFAULT NULL,
  `second` INT NULL DEFAULT NULL,
  `endlocation_x` INT NULL DEFAULT NULL,
  `endlocation_y` INT NULL DEFAULT NULL,
  PRIMARY KEY (`idmatch_event`),
  INDEX `match_idx` (`match` ASC) VISIBLE,
  CONSTRAINT `mec_match_fk`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


-- -----------------------------------------------------
-- Table `scouting`.`match_event_infraction`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `scouting`.`match_event_infraction` (
  `idmatch_event` INT NOT NULL,
  `match` INT NOT NULL,
  `player` INT NULL DEFAULT NULL,
  `matchPeriod` VARCHAR(45) NULL DEFAULT NULL,
  `location_x` INT NULL DEFAULT NULL,
  `location_y` INT NULL DEFAULT NULL,
  `minute` INT NULL DEFAULT NULL,
  `second` INT NULL DEFAULT NULL,
  `yellowCard` TINYINT NULL,
  `redCard` TINYINT NULL,
  PRIMARY KEY (`idmatch_event`),
  INDEX `match_idx` (`match` ASC) VISIBLE,
  CONSTRAINT `mei_match_fk`
    FOREIGN KEY (`match`)
    REFERENCES `scouting`.`match` (`idmatch`))
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8mb3;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
