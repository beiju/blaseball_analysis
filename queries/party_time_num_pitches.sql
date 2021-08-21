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
