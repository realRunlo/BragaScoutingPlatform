'''Module that calculates the rating of a player based on the data collected from the scouting platform.

Isolated so as to be easier to modify and test.'''


def calculate_rating(stats):
    '''Calculates the rating of a player based on the stats provided.'''
    # base value
    rating = 6.0

    # add/subtract based on stats
    rating += stats['total']['goals'] * 0.7
    rating += stats['total']['assists'] * 0.3
    rating += stats['total']['shots'] * 0.05
    rating += stats['total']['shotsOnTarget'] * 0.05
    rating -= stats['total']['yellowCards'] * 0.2
    rating -= stats['total']['redCards'] * 1
    rating -= stats['total']['directRedCards'] * 0.8
    rating -= (stats['total']['penalties']-stats['total']['successfulPenalties']) * 0.5
    rating += stats['total']['successfulLinkupPlays'] * 0.04
    rating -= (stats['total']['linkupPlays']-stats['total']['successfulLinkupPlays']) * 0.01
    rating += stats['total']['duelsWon'] * 0.02
    rating -= (stats['total']['duels']-stats['total']['duelsWon']) * 0.01
    rating -= (stats['total']['defensiveDuels']-stats['total']['defensiveDuelsWon']) * 0.04
    rating += stats['total']['offensiveDuelsWon'] * 0.03
    rating += stats['total']['aerialDuelsWon'] * 0.02
    rating -= (stats['total']['aerialDuels']-stats['total']['aerialDuelsWon']) * 0.02
    rating += stats['total']['successfulPasses'] * 0.003
    rating -= (stats['total']['passes']-stats['total']['successfulPasses']) * 0.015
    rating += stats['total']['successfulSmartPasses'] * 0.03
    rating += stats['total']['successfulPassesToFinalThird'] * 0.005
    rating += stats['total']['successfulCrosses'] * 0.06
    rating -= (stats['total']['crosses']-stats['total']['successfulCrosses']) * 0.015
    rating += stats['total']['successfulForwardPasses'] * 0.002
    rating -= (stats['total']['backPasses']-stats['total']['successfulBackPasses']) * 0.02
    rating += stats['total']['successfulThroughPasses'] * 0.01
    rating += stats['total']['successfulKeyPasses'] * 0.05
    rating += stats['total']['successfulVerticalPasses'] * 0.002
    rating += stats['total']['successfulLongPasses'] * 0.005
    rating -= (stats['total']['longPasses']-stats['total']['successfulLongPasses']) * 0.008
    rating -= (stats['total']['lateralPasses']-stats['total']['successfulLateralPasses']) * 0.01
    rating += stats['total']['successfulDribbles'] * 0.05
    rating -= (stats['total']['dribbles']-stats['total']['successfulDribbles']) * 0.03
    rating += stats['total']['interceptions'] * 0.02
    rating += stats['total']['successfulDefensiveAction'] * 0.025
    rating -= (stats['total']['defensiveActions']-stats['total']['successfulDefensiveAction']) * 0.03
    rating += stats['total']['successfulAttackingActions'] * 0.02
    rating -= (stats['total']['attackingActions']-stats['total']['successfulAttackingActions']) * 0.01
    rating += stats['total']['freeKicksOnTarget'] * 0.01
    rating -= (stats['total']['freeKicks']-stats['total']['freeKicksOnTarget']) * 0.01
    rating += stats['total']['directFreeKicksOnTarget'] * 0.02
    rating -= (stats['total']['directFreeKicks']-stats['total']['directFreeKicksOnTarget']) * 0.01
    rating += stats['total']['accelerations'] * 0.03
    rating += stats['total']['pressingDuelsWon'] * 0.02
    rating -= (stats['total']['pressingDuels']-stats['total']['pressingDuelsWon']) * 0.01
    rating += stats['total']['looseBallDuelsWon'] * 0.01
    rating -= (stats['total']['looseBallDuels']-stats['total']['looseBallDuelsWon']) * 0.01
    rating -= stats['total']['missedBalls'] * 0.03
    rating += stats['total']['shotAssists'] * 0.03
    rating += stats['total']['shotOnTargetAssists'] * 0.02
    rating += stats['total']['recoveries'] * 0.03
    rating += stats['total']['opponentHalfRecoveries'] * 0.03
    rating += stats['total']['dangerousOpponentHalfRecoveries'] * 0.03
    rating += stats['total']['counterpressingRecoveries'] * 0.01
    rating -= stats['total']['losses'] * 0.015
    rating -= stats['total']['ownHalfLosses'] * 0.04
    rating -= stats['total']['dangerousOwnHalfLosses'] * 0.05
    rating += stats['total']['receivedPass'] * 0.001
    rating += stats['total']['touchInBox'] * 0.05
    rating += stats['total']['progressiveRun'] * 0.045
    rating -= stats['total']['offsides'] * 0.01
    rating += stats['total']['clearances'] * 0.02
    rating += stats['total']['secondAssists'] * 0.07
    rating += stats['total']['thirdAssists'] * 0.02
    rating += stats['total']['shotsBlocked'] * 0.01
    rating += stats['total']['foulsSuffered'] * 0.02
    rating += stats['total']['successfulProgressivePasses'] * 0.025
    rating += stats['total']['successfulSlidingTackles'] * 0.02
    rating -= (stats['total']['slidingTackles']-stats['total']['successfulSlidingTackles']) * 0.02
    rating += stats['total']['dribblesAgainstWon'] * 0.03
    rating -= (stats['total']['dribblesAgainst']-stats['total']['dribblesAgainstWon']) * 0.04
    rating -= (stats['total']['goalKicks']-stats['total']['successfulGoalKicks']) * 0.04
    rating += stats['total']['successfulGoalKicks'] * 0.01
    rating += stats['total']['gkCleanSheets'] * 0.4
    rating -= stats['total']['gkConcededGoals'] * 0.1
    rating -= (stats['total']['gkExits']-stats['total']['gkSuccessfulExits']) * 0.03
    rating += stats['total']['gkSuccessfulExits'] * 0.03
    rating -= (stats['total']['gkAerialDuels']-stats['total']['gkAerialDuelsWon']) * 0.02
    rating += stats['total']['gkAerialDuelsWon'] * 0.02
    rating += stats['total']['gkSaves'] * 0.1
            
    # limit rating to 10
    if rating > 10:
        rating = 10
        
    # round to 1 decimal place
    return round(rating, 1)


