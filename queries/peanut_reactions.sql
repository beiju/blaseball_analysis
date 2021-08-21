-- very accused query to find peanut reactions
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
