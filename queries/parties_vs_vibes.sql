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
