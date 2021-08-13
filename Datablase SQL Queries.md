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

very accused query to find peanut reactions
```postgresql
SELECT badq.*, goodq.good  FROM (SELECT team, COUNT(team) AS bad
FROM (SELECT (CASE WHEN team='Dalé' THEN 'Dale' ELSE team END) AS team 
	  FROM (SELECT substring(original_text from '^(.*?) hitter') AS team 
	  		FROM data.outcomes 
	  		WHERE event_type='PEANUT_BAD') inn

UNION ALL 
	  SELECT * FROM (VALUES ('Dale'), ('Wild Wings')) AS t (team)
UNION ALL 

SELECT nickname AS team FROM (
	SELECT game_event_id, substring(original_text from '^(.*?) swallowed') AS player_name
	FROM data.outcomes 
	WHERE event_type='PEANUT_BAD' 
		AND original_text NOT LIKE '%hitter%'
		AND original_text NOT LIKE '%pitcher%') q 
LEFT JOIN data.game_events ON q.game_event_id=game_events.id
INNER JOIN data.players ON players.player_name=q.player_name 
	AND players.valid_from <= perceived_at
	AND (players.valid_until >= perceived_at OR players.valid_until IS NULL)
INNER JOIN data.team_roster ON players.player_id=team_roster.player_id
	AND team_roster.tournament=-1
	AND team_roster.valid_from <= perceived_at
	AND (team_roster.valid_until >= perceived_at OR team_roster.valid_until IS NULL)
LEFT JOIN data.teams ON teams.team_id=team_roster.team_id 
	AND teams.valid_until IS NULL) qq
GROUP BY team
ORDER BY COUNT(team) DESC) badq

FULL OUTER JOIN (SELECT * FROM (SELECT team, COUNT(team) AS good
FROM (SELECT (CASE WHEN team='Dalé' THEN 'Dale' ELSE team END) AS team 
	  FROM (SELECT substring(original_text from '^(.*?) hitter') AS team 
	  		FROM data.outcomes 
	  		WHERE event_type='PEANUT_GOOD') inn

UNION ALL 
	  SELECT * FROM (VALUES ('Dale'), ('Wild Wings')) AS t (team)
UNION ALL 

SELECT nickname AS team FROM (
	SELECT game_event_id, substring(original_text from '^(.*?) swallowed') AS player_name
	FROM data.outcomes 
	WHERE event_type='PEANUT_GOOD' 
		AND original_text NOT LIKE '%hitter%'
		AND original_text NOT LIKE '%pitcher%') q 
LEFT JOIN data.game_events ON q.game_event_id=game_events.id
INNER JOIN data.players ON players.player_name=q.player_name 
	AND players.valid_from <= perceived_at
	AND (players.valid_until >= perceived_at OR players.valid_until IS NULL)
INNER JOIN data.team_roster ON players.player_id=team_roster.player_id
	AND team_roster.tournament=-1
	AND team_roster.valid_from <= perceived_at
	AND (team_roster.valid_until >= perceived_at OR team_roster.valid_until IS NULL)
LEFT JOIN data.teams ON teams.team_id=team_roster.team_id 
	AND teams.valid_until IS NULL) qq
GROUP BY team
ORDER BY COUNT(team) DESC) oq) goodq ON goodq.team=badq.team
```

strength of underhanded on pitchers
```postgresql

select * 
from (select runs_groups.*, 
		runs_by_hr/runs as proportion, 
		player_name,
		rank() over (order by runs_by_hr/runs desc) as rank
	from (
		select pitcher_id,
			sum(runs_batted_in) AS runs,
			sum((case when event_type='HOME_RUN' or event_type='HOME_RUN_5' then runs_batted_in else 0 end)) as runs_by_hr
		from data.game_events
		where season=19
		group by pitcher_id) runs_groups
	left join data.players on pitcher_id=player_id and players.valid_until is null
	order by runs_by_hr/runs desc) ranked_pitchers
where player_name in ('Dunlap Figueroa',
'Adalberto Tosser',
'Mindy Kugel',
'Miguel James',
'King Weatherman',
'Winnie Hess',
'Juice Collins',
'Alexandria Rosales',
'Baldwin Breadwinner',
'Riley Firewall',
'Snyder Briggs',
'Nolanestophia Patterson',
'Patchwork Southwick',
'Ziwa Mueller', 'Wanda Schenn', 'Mindy Salad')
```

longest time with mod
```postgresql
SELECT * FROM (SELECT player_name, 
			   AGE((case when mods.valid_until is null then now() else mods.valid_until end), mods.valid_from) as duration
		FROM data.player_modifications mods
		LEFT JOIN data.players ON players.player_id=mods.player_id
		WHERE modification='ELSEWHERE'
			AND players.valid_until IS NULL) q
ORDER BY duration DESC
LIMIT 30
```

big buckets moxie correlation
```postgresql
select 
	COUNT(*) AS num_homers,
	SUM((array_to_string(event_text, '; ') LIKE '%The ball lands in a Big Bucket%')::int) AS num_buckets, 
	round(moxie, 1) AS moxie
from data.game_events
left join data.games on game_events.game_id=games.game_id
inner join data.stadiums on stadiums.team_id=games.home_team
	and stadiums.valid_from <= game_events.perceived_at
	and (stadiums.valid_until > game_events.perceived_at OR stadiums.valid_until IS NULL)
	and stadiums.team_id<>'8d87c468-699a-47a8-b40d-cfb73a5660ad' -- necessary thanks to crabs big bucket fraud
inner join data.stadium_modifications on stadiums.stadium_id=stadium_modifications.stadium_id
	and stadium_modifications.valid_from <= game_events.perceived_at
	and (stadium_modifications.valid_until > game_events.perceived_at OR stadium_modifications.valid_until IS NULL)
	and stadium_modifications.modification='big_bucket_mod'
inner join data.players on game_events.batter_id=players.player_id
	and players.valid_from <= game_events.perceived_at
	and (players.valid_until > game_events.perceived_at OR players.valid_until IS NULL)
where event_type='HOME_RUN' or event_type='HOME_RUN_5'
group by round(moxie, 1)
--limit 10

```


alley oops rate
```postgresql
select 
	player_id,
	count(*) as num_oops,
	sum(slammed_it_down::int) as num_successful
from (select coalesce(next_in_roster, first_in_roster) as ooper, slammed_it_down, perceived_at
	from (select 
		  	perceived_at,
			(select player_id
			 from data.team_roster team_roster_next
			 where team_roster_next.team_id=team_roster.team_id
				and position_type_id=0
				and team_roster_next.valid_from <= game_events.perceived_at
				and (team_roster_next.valid_until > game_events.perceived_at or team_roster_next.valid_until is null)
				and team_roster_next.position_id > team_roster.position_id
				order by position_id
				limit 1) as next_in_roster,
			(select player_id
			 from data.team_roster team_roster_next
			 where team_roster_next.team_id=team_roster.team_id
				and position_type_id=0
				and team_roster_next.valid_from <= game_events.perceived_at
				and (team_roster_next.valid_until > game_events.perceived_at or team_roster_next.valid_until is null)
				and team_roster_next.position_id=0) as first_in_roster,
			array_to_string(event_text, '; ') LIKE '%went up for the alley oop%' AS went_for_it, 
			array_to_string(event_text, '; ') LIKE '%they slammed it down for%' AS slammed_it_down
		from data.game_events
		left join data.games on game_events.game_id=games.game_id
		inner join data.stadiums on stadiums.team_id=games.home_team
			and stadiums.valid_from <= game_events.perceived_at
			and (stadiums.valid_until > game_events.perceived_at OR stadiums.valid_until IS NULL)
			and stadiums.team_id<>'8d87c468-699a-47a8-b40d-cfb73a5660ad' -- necessary thanks to crabs big bucket fraud
		inner join data.stadium_modifications on stadiums.stadium_id=stadium_modifications.stadium_id
			and stadium_modifications.valid_from <= game_events.perceived_at
			and (stadium_modifications.valid_until > game_events.perceived_at OR stadium_modifications.valid_until IS NULL)
			and stadium_modifications.modification='hoops_mod'
		left join data.team_roster on game_events.batter_id=team_roster.player_id
			and team_roster.tournament=-1
			and team_roster.valid_from <= game_events.perceived_at
			and (team_roster.valid_until > game_events.perceived_at OR team_roster.valid_until IS NULL)
		where (event_type='HOME_RUN' or event_type='HOME_RUN_5')
			and array_to_string(event_text, '; ') LIKE '%went up for the alley oop%') q
	where went_for_it) qq
left join data.players on ooper=players.player_id
	and players.valid_from <= perceived_at
	and (players.valid_until > perceived_at OR players.valid_until IS NULL)
group by player_id
order by count(*) - sum(slammed_it_down::int) desc
```

tunnels rate per team
```postgresql
select sum(1.0 / num_eligible) as num_events, 
	sum((event_text like concat('%', player_name, ' entered the Tunnels%'))::int) as num_tunnels, 
	team_id,
	nickname
from (select unnest(event_text) as event_text, player_id, perceived_at, team_id, nickname, num_eligible
	from (select game_events.event_text, 
		  team_roster.player_id, 
		  game_events.perceived_at, 
		  teams.team_id, 
		  teams.nickname,
		  count(*) over (partition by game_events.id) as num_eligible
		from data.game_events
		left join data.games on game_events.game_id=games.game_id
		left join data.team_roster on team_roster.team_id=games.home_team
			and team_roster.tournament=-1
			and team_roster.position_type_id=1
			and team_roster.player_id <> games.winning_pitcher_id
			and team_roster.player_id <> games.losing_pitcher_id
			and team_roster.valid_from <= game_events.perceived_at
			and (team_roster.valid_until > game_events.perceived_at or team_roster.valid_until is null)
		inner join data.teams on team_roster.team_id=teams.team_id
			and teams.valid_from <= game_events.perceived_at
			and (teams.valid_until > game_events.perceived_at or teams.valid_until is null)
		inner join taxa.event_types on game_events.event_type=event_types.event_type
		where ((game_events.season=19 and game_events.day > 71) or game_events.season > 19)
			and plate_appearance>0
		 	and game_events.away_score >= 1) qq) q
left join data.players on q.player_id=players.player_id
	and players.valid_from <= q.perceived_at
	and (players.valid_until > q.perceived_at or players.valid_until is null)
group by team_id, nickname
limit 100
```

tunnels steals
```postgresql
select --sum(1.0 / num_eligible) as num_events, 
	--sum((event_text like concat('%', thief.player_name, ' entered the Tunnels%'))::int) as num_tunnels, 
	victim.watchfulness,
	victim.player_name,
	thief.player_name,
	event_text
from (select unnest(event_text) as event_text, player_id, perceived_at, num_eligible, defending_pitcher
	from (select game_events.event_text, 
		  team_roster.player_id, 
		  game_events.perceived_at, 
		  count(*) over (partition by game_events.id) as num_eligible,
		  (case when games.home_score > games.away_score then losing_pitcher_id else winning_pitcher_id end) as defending_pitcher
		from data.game_events
		left join data.games on game_events.game_id=games.game_id
		left join data.team_roster on team_roster.team_id=games.home_team
			and team_roster.tournament=-1
			and team_roster.position_type_id=1
			and team_roster.player_id <> games.winning_pitcher_id
			and team_roster.player_id <> games.losing_pitcher_id
			and team_roster.valid_from <= game_events.perceived_at
			and (team_roster.valid_until > game_events.perceived_at or team_roster.valid_until is null)
		inner join taxa.event_types on game_events.event_type=event_types.event_type
		where ((game_events.season=19 and game_events.day > 71) or game_events.season > 19)
			and plate_appearance>0) qq) q
left join data.players thief on q.player_id=thief.player_id
	and thief.valid_from <= q.perceived_at
	and (thief.valid_until > q.perceived_at or thief.valid_until is null)
left join data.players victim on q.defending_pitcher=victim.player_id
	and victim.valid_from <= q.perceived_at
	and (victim.valid_until > q.perceived_at or victim.valid_until is null)
where event_text like concat('%', thief.player_name, ' entered the Tunnels%')
order by victim.watchfulness
limit 30
```

voicemails
```postgresql
select 
	nickname,
	sum((q.highest_score=0 and q.lowest_score=0)::int) as score_always_0,
	sum((q.highest_score=0)::int) as score_never_above_0,
	sum((games.home_score=0)::int) as score_ended_at_0
from (select game_id, max(home_score) as highest_score, min(home_score) as lowest_score from data.game_events
	where game_events.season=19
	group by game_id) q
left join data.games on games.game_id=q.game_id
left join data.teams on games.home_team=teams.team_id and teams.valid_until is null
group by team_id, nickname
order by sum((q.highest_score=0 and q.lowest_score=0)::int) desc
```

incin rate
```postgresql
select sum((modification is null)::int) as natural_events,
	   sum((modification is not null)::int) as unstable_events,
	   sum((incin and modification is null)::int) as natural_incins,
	   sum((incin and modification is not null)::int) as unstable_incins,
	   season_,
	   position_type_id
from (select EXISTS (
		SELECT -- can be empty 
		FROM unnest(event_text) elem
		WHERE elem LIKE '%incinerated%'
			and (elem like concat('%hitter ', player_name, '!%')
				 or elem like concat('%pitcher ', player_name, '!%')
				 or elem like concat('%incinerated ', player_name, '!%'))
	  ) as incin,
	  games.season as season_,
		*
	from data.game_events
	left join data.games on game_events.game_id=games.game_id
	left join data.team_roster on (games.home_team=team_roster.team_id or games.away_team=team_roster.team_id)
		and (team_roster.position_type_id=0 or team_roster.position_type_id=1)
		and team_roster.valid_from <= game_events.perceived_at
		and (team_roster.valid_until > game_events.perceived_at or team_roster.valid_until is null)
	left join data.player_modifications on player_modifications.player_id=team_roster.player_id
		and modification='MARKED' /* unstable */
		and player_modifications.valid_from <= game_events.perceived_at
		and (player_modifications.valid_until > game_events.perceived_at or player_modifications.valid_until is null)
	left join data.players on players.player_id=team_roster.player_id
		and players.valid_from <= game_events.perceived_at
		and (players.valid_until > game_events.perceived_at or players.valid_until is null)
	where games.weather=7 /* solar eclipse */
		  ) q
group by season_, position_type_id
order by season_, position_type_id
```

finnesse (of players with at least 5 games, per season during all pre-underhanded expansion era seasons)
```postgresql
select round(baserunners_stranded / runs_allowed, 3) as finnesse,
	round(runs_allowed, 1) as runs_allowed,
	baserunners_stranded, 
	games,
	player_name,
	q.season + 1 as season_one_indexed
from (select count(*) as baserunners_stranded, pitcher_id, season
	from data.game_events 
	inner join data.game_event_base_runners on game_events.id=game_event_base_runners.game_event_id
	where (outs_before_play + outs_on_play = 3)
	group by pitcher_id, season) q
left join (
	select sum(games) as games, sum(runs_allowed) as runs_allowed, player_id, player_name, season
	from data.pitching_stats_player_season 
	group by player_id, player_name, season) stats 
	on q.pitcher_id=stats.player_id and q.season=stats.season
where runs_allowed > 0 and games > 5 and q.season < 19 and q.season > 10
order by baserunners_stranded / runs_allowed desc
```

winnrate (win rate against winnie hess, expansion era only)
```postgresql
select winnie_wins_grouped.team, full_name, wins, losses, round(wins/(wins+losses+0.0), 3) as winnrate
from (select team, count(*) as wins
	from (select 
			(case when home_score > away_score then home_team else away_team end) as team
		from data.games 
		where losing_pitcher_id='f2a27a7e-bf04-4d31-86f5-16bfa3addbe7'
			and season > 11) winnie_wins
	group by team) winnie_wins_grouped
full outer join (select team, count(*) as losses
	from (select 
			(case when home_score < away_score then home_team else away_team end) as team
		from data.games 
		where winning_pitcher_id='f2a27a7e-bf04-4d31-86f5-16bfa3addbe7'
			and season > 11) winnie_losses
	group by team) winnie_losses_grouped on winnie_wins_grouped.team=winnie_losses_grouped.team
left join data.teams on winnie_wins_grouped.team=teams.team_id and teams.valid_until is null
order by wins/(wins+losses+0.0) desc
```

season 23 pitcher performance stats by attribute
```postgresql
select stats.*, 
	players.player_name,
	(walks + hits) / (outs / 3.0) as whip,
	hits / (outs / 27.0) as h9,
	home_runs / (outs / 27.0) as hr9,
	walks / (outs / 27.0) as bb9,
	strikeouts / (outs / 27.0) as so9,
	(case when walks=0 then 0 else strikeouts / (walks * 1.0) end) as so_bb
from (select pitcher_id, coldness, overpowerment, ruthlessness, shakespearianism, suppression, unthwackability,
		count(*) as game_events,
		count(*) filter (where event_types.out=1) as outs,
		count(*) filter (where game_events.event_type='STRIKEOUT') as strikeouts,
		count(*) filter (where game_events.event_type='WALK') as walks,
		count(*) filter (where event_types.hit=1) as hits,
		count(*) filter (where game_events.event_type='HOME_RUN' or game_events.event_type='HOME_RUN_5') as home_runs
	from data.game_events 
	left join taxa.event_types on game_events.event_type=event_types.event_type
	left join data.players on game_events.pitcher_id=players.player_id
		and players.valid_from <= game_events.perceived_at 
		and (players.valid_until > game_events.perceived_at or players.valid_until is NULL)
	where season=22 and pitcher_id is not null
	group by pitcher_id, coldness, overpowerment, ruthlessness, shakespearianism, suppression, unthwackability
) stats
-- Getting players outside the stats subquery so stats aren't grouped by name changes
left join data.players on stats.pitcher_id=players.player_id and players.valid_until is null
where outs > 0

```