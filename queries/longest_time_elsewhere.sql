SELECT * FROM (SELECT player_name,
			   AGE((case when mods.valid_until is null then now() else mods.valid_until end), mods.valid_from) as duration
		FROM data.player_modifications mods
		LEFT JOIN data.players ON players.player_id=mods.player_id
		WHERE modification='ELSEWHERE'
			AND players.valid_until IS NULL) q
ORDER BY duration DESC
LIMIT 30
