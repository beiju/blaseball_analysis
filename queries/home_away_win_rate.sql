SELECT a.season, home_wins, away_wins FROM
    (SELECT season, COUNT(*) AS home_wins FROM data.games WHERE home_score > away_score GROUP BY season) a
        INNER JOIN
    (SELECT season, COUNT(*) AS away_wins FROM data.games WHERE home_score < away_score GROUP BY season) b
        ON a.season = b.season
ORDER BY a.season
