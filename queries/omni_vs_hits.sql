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
