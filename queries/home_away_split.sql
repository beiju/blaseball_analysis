SELECT n.season, MAX(n.games) AS max_home_games, MIN(n.games) AS min_home_games FROM
	(SELECT season, home_team, COUNT(*) as games FROM data.games WHERE day < 99 GROUP BY season, home_team ) AS n
	GROUP BY n.season
	ORDER BY n.season
