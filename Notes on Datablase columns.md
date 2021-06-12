Notes on Datablase columns
==========================

game_events
-----------

* `is_pinch_hit`: Always false (for now)
* `is_sacrifice_fly` and `is_sacrifice_hit`: If `event_type` is `SACRIFICE`, 
  exactly one of these is true
  * `is_sacrifice_fly`: game event text is "\<batter name> hit a sacrifice fly. 
    <runner name> tags up and scores"
  * `is_sacrifice_hit`: game event text is "\<runner name> scores on the 
    sacrifice"
* `batted_ball_type`: (null or empty string) <=> ball not in play. 
  If ball is in play:
  * `FLY`: Cross-reference with `event_type`:
      * `HOME_RUN`: Is a home run. Includes grand slams.
      * `HOME_RUN_5`: Is a home run while 5th base is active.
      * `SACRIFICE`: Sac fly. `is_sacrifice_fly` is true. However, sometimes a 
        sac fly has `batted_ball_type` of `UNKNOWN`. I don't know why. 
        `is_sacrifice_fly` is a reliable indicator of sac flies.
      * `OUT`: Flyout
      * `WALK`: Data entry error? Only 2 records, can probably ignore
      * `SECRET_BASE_ENTER`: Data entry error? Only 1 record
  * `GROUNDER`: Cross-reference with `event_type`:
      * `OUT`: Ground out
      * `SACRIFICE`: Sac hit. Exactly equivalent to `is_sacrifice_hit`
      * `WALK`: Data entry error. 4 records
      * `STRIKEOUT`: Data entry error. 10 records
  * `UNKNOWN`: If `event_type` is `SACRIFICE`, then equivalent to `FLY`. 
    Otherwise, is a non-HR hit (single, double, triple, or quadruple).
* `is_bunt`: Always false (for now)
* `errors_on_play`: Always 0 (for now)
* `event_type`:
  * `OUT`: flyout, ground out, double play, bird out, siphon out, or data entry 
    error (100-ish instances, of which 50-ish can be filtered out by checking 
    `outs_on_play>0`)
  * `UNKNOWN_OUT`: Dummy row inserted when the outs count increases but we don't
    have an event that says why.
  * `UNKNOWN`: Seems to be non-baseball blaseball events. Psychoacoustics, 
    Elsewhere, A Blood, "Play Ball!", targeted shame, home field advantage, ...
* Fielding out `event_types`: `FIELDERS_CHOICE`, `SACRIFICE`, `OUT` (note that 
  strikeouts are a different `EVENT_TYPE`)
