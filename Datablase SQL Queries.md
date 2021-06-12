Home and away team win rate by season
```SQL
SELECT a.season, home_wins, away_wins FROM
    (SELECT season, COUNT(*) AS home_wins FROM data.games WHERE home_score > away_score GROUP BY season) a
        INNER JOIN 
    (SELECT season, COUNT(*) AS away_wins FROM data.games WHERE home_score < away_score GROUP BY season) b
        ON a.season = b.season
ORDER BY a.season
```

Highest and lowest number of home games for a team by season
```SQL
SELECT n.season, MAX(n.games) AS max_home_games, MIN(n.games) AS min_home_games FROM
	(SELECT season, home_team, COUNT(*) as games FROM data.games WHERE day < 99 GROUP BY season, home_team ) AS n
	GROUP BY n.season
	ORDER BY n.season
```

Number of pitches each team has seen while being eligible for party time
```sql
SELECT 
		batter_team_id, 
		SUM(total_strikes + total_fouls + total_balls) AS num_pitches
	FROM data.game_events
	FULL JOIN data.team_modifications ON game_events.batter_team_id=team_modifications.team_id
	WHERE tournament=-1 
		AND team_modifications.valid_from<game_events.perceived_at 
		AND (team_modifications.valid_until>game_events.perceived_at OR team_modifications.valid_until IS NULL)
		AND team_modifications.modification='PARTY_TIME'
	GROUP BY batter_team_id
```

Does stadium mysticism affect party rate? [No.]
```postgresql
SELECT 
		stadiums.mysticism,
		SUM(cardinality(pitches) * ((btm.modification IS NOT NULL)::int + (ptm.modification IS NOT NULL)::int)) AS num_pitches,
		SUM(cardinality(event_text) * ((btm.modification IS NOT NULL)::int + (ptm.modification IS NOT NULL)::int)) AS num_sub_events,
		SUM((SELECT count(*) FROM unnest(event_text) AS e WHERE e LIKE '% is Partying!')) as parties
	FROM data.game_events
	LEFT JOIN (SELECT team_id, valid_from, valid_until, modification 
				FROM data.team_modifications) ptm 
				ON ptm.team_id=game_events.pitcher_team_id
					AND ptm.valid_from<game_events.perceived_at 
					AND (ptm.valid_until>game_events.perceived_at OR ptm.valid_until IS NULL)
					AND ptm.modification='PARTY_TIME'
	LEFT JOIN (SELECT team_id, valid_from, valid_until, modification 
				FROM data.team_modifications) btm 
				ON btm.team_id=game_events.batter_team_id
					AND btm.valid_from<game_events.perceived_at 
					AND (btm.valid_until>game_events.perceived_at OR btm.valid_until IS NULL)
					AND btm.modification='PARTY_TIME'
	INNER JOIN data.games ON games.game_id=game_events.game_id
	INNER JOIN data.stadiums ON stadiums.team_id=games.home_team
	WHERE game_events.tournament=-1 
		AND stadiums.valid_from<game_events.perceived_at 
		AND (stadiums.valid_until>game_events.perceived_at OR stadiums.valid_until IS NULL)
	GROUP BY stadiums.mysticism
```

Do vibe-related quantities affect party rate? (Answer: None of the ones tested so far.)
```postgresql
SELECT vibe_range, SUM(num_pitches) AS num_pitches, SUM(num_sub_events) AS num_sub_events, SUM(parties) AS parties FROM (
	SELECT 
			ROUND((cinnamon + pressurization)::numeric, 1) AS vibe_range,
			cardinality(pitches) * (btm.modification IS NOT NULL)::int AS num_pitches,
			cardinality(event_text) * (btm.modification IS NOT NULL)::int AS num_sub_events,
			(SELECT COUNT(e) FROM UNNEST(event_text) AS e WHERE e=CONCAT(player_name, ' is Partying!')) as parties
		FROM data.game_events
		FULL JOIN data.team_roster ON team_roster.team_id=game_events.batter_team_id
		LEFT JOIN data.players ON players.player_id=team_roster.player_id
		LEFT JOIN (SELECT team_id, valid_from, valid_until, modification 
					FROM data.team_modifications) btm 
					ON btm.team_id=game_events.batter_team_id
						AND btm.valid_from<game_events.perceived_at 
						AND (btm.valid_until>game_events.perceived_at OR btm.valid_until IS NULL)
						AND btm.modification='PARTY_TIME'
		WHERE game_events.tournament=-1 
			AND team_roster.valid_from<game_events.perceived_at 
			AND (team_roster.valid_until>game_events.perceived_at OR team_roster.valid_until IS NULL)
			AND players.valid_from<game_events.perceived_at 
			AND (players.valid_until>game_events.perceived_at OR players.valid_until IS NULL)
			AND (position_type_id=0 OR position_type_id=1)
			
	UNION ALL
	
	SELECT 
			ROUND((cinnamon + pressurization)::numeric, 1) AS vibe_range,
			cardinality(pitches) * (btm.modification IS NOT NULL)::int AS num_pitches,
			cardinality(event_text) * (btm.modification IS NOT NULL)::int AS num_sub_events,
			(SELECT COUNT(e) FROM UNNEST(event_text) AS e WHERE e=CONCAT(player_name, ' is Partying!')) as parties
		FROM data.game_events
		FULL JOIN data.team_roster ON team_roster.team_id=game_events.pitcher_team_id
		LEFT JOIN data.players ON players.player_id=team_roster.player_id
		LEFT JOIN (SELECT team_id, valid_from, valid_until, modification 
					FROM data.team_modifications) btm 
					ON btm.team_id=game_events.pitcher_team_id
						AND btm.valid_from<game_events.perceived_at 
						AND (btm.valid_until>game_events.perceived_at OR btm.valid_until IS NULL)
						AND btm.modification='PARTY_TIME'
		WHERE game_events.tournament=-1 
			AND team_roster.valid_from<game_events.perceived_at 
			AND (team_roster.valid_until>game_events.perceived_at OR team_roster.valid_until IS NULL)
			AND players.valid_from<game_events.perceived_at 
			AND (players.valid_until>game_events.perceived_at OR players.valid_until IS NULL)
			AND (position_type_id=0 OR position_type_id=1)
	) q
	GROUP BY vibe_range
	ORDER BY vibe_range
```

Is omniscience real?
```postgresql
SELECT h9pr, SUM(outs_on_play) as outs, (SUM(hits)*1.0 / NULLIF(SUM(outs_on_play), 0)) * 27 AS h9, omni
	FROM (
	SELECT 	ROUND(-2.33 * unthwackability -3.33 * ruthlessness -0.30 * overpowerment + 14.47, 1) AS h9pr,
			outs_on_play,
			(bases_hit>0)::int AS hits,
			player_name,
			ROUND((SELECT AVG(omniscience)
				FROM data.team_roster AS r
				INNER JOIN data.players AS pl ON r.player_id=pl.player_id
				WHERE r.team_id=game_events.pitcher_team_id
					AND r.position_type_id=0
					AND r.valid_from<=game_events.perceived_at 
					AND (r.valid_until>game_events.perceived_at OR r.valid_until IS NULL)
					AND pl.valid_from<=game_events.perceived_at 
					AND (pl.valid_until>game_events.perceived_at OR pl.valid_until IS NULL)
			), 2) AS omni
		FROM data.game_events
		INNER JOIN data.players 
			ON players.player_id=game_events.pitcher_id 
			AND players.valid_from<=game_events.perceived_at 
			AND (players.valid_until>game_events.perceived_at OR players.valid_until IS NULL)
		WHERE season=17
	) q
	GROUP BY h9pr, omni
	HAVING SUM(hits)>0
	ORDER BY outs ASC
```

Monster query that selects every attribute and every stat that we think is
correlated with it
```postgresql
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
```
