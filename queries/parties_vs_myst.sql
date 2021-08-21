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
