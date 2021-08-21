-- Monster query that selects every attribute and every stat that we think is
-- correlated with it

SELECT
	-- Batting (current batter)
	batter.buoyancy,
	batter.divinity,
	batter.martyrdom,
	batter.moxie,
	batter.musclitude,
	batter.patheticism,
	batter.thwackability,
	batter.tragicness AS batter_tragicness, -- it could apply while batting or while running
	batter.ground_friction, -- it lives in baserunning but it applies while batting

	-- Pitching (current pitcher)
	pitcher.coldness,
	pitcher.overpowerment,
	pitcher.ruthlessness,
	pitcher.shakespearianism,
	pitcher.suppression,
	pitcher.unthwackability,

	-- Baserunning (foremost baserunner, if any)
	baserunner.base_thirst,
	baserunner.laserlikeness,
	baserunner.continuation,
	-- not including groundfriction here because it applies while batting
	baserunner.indulgence,
	baserunner.tragicness AS baserunner_tragicness, -- it could apply while batting or while running

	-- Defense: Average of pitcher's team's batters and pitcher
	defense.*, -- defense stats are already selected by the subquery

	-- CURRENT BATTER METRICS

	-- Buoyancy: fielded outs, flyouts
	event_type IN ('FIELDERS_CHOICE', 'SACRIFICE', 'OUT') AS is_fielding_out,
	(batted_ball_type='FLY' AND event_type='OUT') OR is_sacrifice_fly AS is_flyout,

	-- Divinity: ball in play, home run
	event_type IN ('HOME_RUN', 'HOME_RUN_5') AS is_home_run, -- includes grand slams
	batted_ball_type IS NOT NULL AND batted_ball_type<>'' AS ball_in_play,

	-- Martyrdom: runner on base, fielder's choice, runner advances
	baserunner.player_id IS NOT NULL AS runner_on_base,
	base_before_play+2 >= (CASE WHEN top_of_inning THEN away_base_count ELSE home_base_count END)
		AND baserunner.player_id IS NOT NULL
		AS runner_in_scoring_position,
	event_type='FIELDERS_CHOICE' AS is_fielders_choice,
	base_before_play IS NOT NULL AND base_after_play>base_before_play AS runner_advances,
	runner_scored,
	GREATEST(0, base_after_play - base_before_play) AS runner_bases_advanced,
	base_before_play IS NOT NULL
		AND base_before_play>base_after_play
		AND (is_sacrifice_fly OR is_sacrifice_hit) AS runner_advances_on_sacrifice,
	runner_scored AND (is_sacrifice_fly OR is_sacrifice_hit) AS runner_scored_on_sacrifice,

	-- Moxie: balls, called strikes
	cardinality(array_positions(pitches, 'B')) AS balls,
	cardinality(array_positions(pitches, 'C')) AS called_strikes,

	-- Musclitude: ball in play (done already), doubles, fouls
	event_type='DOUBLE' AS is_double,
	cardinality(array_positions(pitches, 'F')) AS fouls,

	-- Patheticism: swinging strikes, ball in play (done already)
	cardinality(array_positions(pitches, 'S')) AS swinging_strikes,

	-- Thwackability: ball in play (done already), fielding outs (done already)

	-- Tragicness: batter on base (done), double plays
	is_double_play,

	-- Groundfriction: triples, quadruples?, ball in play (done already), fouls (done already)
	event_type='TRIPLE' AS is_triple,
	event_type='QUADRUPLE' AS is_quadruple,

	-- CURRENT PITCHER METRICS
	-- Ruthlessness: same as Moxie (done already)
	-- Overpowerment: contact, HR, triple, double (all done already), single
	event_type='SINGLE' AS is_single,

	-- Unthwackability: same as thwackability (done already)
	-- Shakesperianism: batter on base, double plays (done already)
	-- Suppression: same as buoyancy (done already)
	-- Coldness: idk try it against everything (everything which has been done already)

	-- FRONTMOST BASERUNNER METRICS
	-- Basethirst: on last base, steal attempts, steal successes
	base_before_play+1 = (CASE WHEN top_of_inning THEN away_base_count ELSE home_base_count END)
		AND baserunner.player_id IS NOT NULL
		AS runner_on_last_base,
	baserunner.player_id IS NOT NULL
		AND (was_base_stolen OR was_caught_stealing)
		AS steal_attempt,
	baserunner.player_id IS NOT NULL AND was_base_stolen AS steal_success

	-- Laserlikeness: same as basethirst
	-- Continuation: on last base, sac plays, hard hits, bases advanced, runs scored (all done already)
	-- Indulgence: same as continuation

	-- DEFENDING TEAM DEFENSE METRICS
	-- Anticapitalism: same as basethirst
	-- Chasiness: same as continuation
	-- Omniscience: same as thwackability
	-- Tenaciousness: same as basethirst
	-- Watchfulness: same as basethirst and same as continuation
FROM data.game_events
INNER JOIN data.players AS pitcher
	ON pitcher.player_id=game_events.pitcher_id
	AND pitcher.valid_from<=game_events.perceived_at
	AND (pitcher.valid_until>game_events.perceived_at OR pitcher.valid_until IS NULL)
INNER JOIN data.players AS batter
	ON batter.player_id=game_events.batter_id
	AND batter.valid_from<=game_events.perceived_at
	AND (batter.valid_until>game_events.perceived_at OR batter.valid_until IS NULL)

LEFT JOIN
	(SELECT DISTINCT ON(game_event_id) *
		FROM data.game_event_base_runners
	 	WHERE base_before_play>0 -- Don't include the batter when they get on base
		ORDER BY game_event_id, base_before_play DESC
	) foremost_base_runner
	ON foremost_base_runner.game_event_id=game_events.id

LEFT JOIN data.players AS baserunner
	ON baserunner.player_id=foremost_base_runner.runner_id
	AND baserunner.valid_from<=game_events.perceived_at
	AND (baserunner.valid_until>game_events.perceived_at OR baserunner.valid_until IS NULL)

CROSS JOIN LATERAL (
	SELECT
		AVG(anticapitalism) AS anticapitalism,
		AVG(chasiness) AS chasiness,
		AVG(omniscience) AS omniscience,
		AVG(tenaciousness) AS tenaciousness,
		AVG(watchfulness) AS watchfulness
	FROM (
		SELECT pl.* FROM data.team_roster AS r
		INNER JOIN data.players AS pl ON r.player_id=pl.player_id
		LEFT JOIN data.player_modifications AS modif ON r.player_id=modif.player_id
			AND modif.modification='ELSEWHERE'
			AND modif.valid_from<=game_events.perceived_at
			AND (modif.valid_until>game_events.perceived_at OR modif.valid_until IS NULL)
		WHERE r.team_id=game_events.pitcher_team_id
			AND r.position_type_id=0
			AND r.valid_from<=game_events.perceived_at
			AND (r.valid_until>game_events.perceived_at OR r.valid_until IS NULL)
			AND pl.valid_from<=game_events.perceived_at
			AND (pl.valid_until>game_events.perceived_at OR pl.valid_until IS NULL)
			AND modification IS NULL

		UNION ALL

		SELECT pl.* FROM data.players AS pl WHERE pl.player_id=game_events.pitcher_id
			AND pl.valid_from<=game_events.perceived_at
			AND (pl.valid_until>game_events.perceived_at OR pl.valid_until IS NULL)
	) q
) AS defense
WHERE game_events.tournament=-1
LIMIT 100
