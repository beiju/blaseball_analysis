select games.season,
       games.day,
       away_team.nickname,
       games.away_score,
       home_team.nickname,
       games.home_score,
       hype
from data.games
         left join (select game_id, min(perceived_at) as perceived_at
                    from data.game_events
                    group by game_id) ge on ge.game_id = games.game_id
         inner join data.stadiums on stadiums.team_id = games.home_team
    and stadiums.valid_from <= ge.perceived_at
    and (stadiums.valid_until > ge.perceived_at or stadiums.valid_until is null)
         left join data.teams home_team on home_team.team_id = games.home_team
    and home_team.valid_from <= ge.perceived_at
    and (home_team.valid_until > ge.perceived_at or
         home_team.valid_until is null)
         left join data.teams away_team on away_team.team_id = games.away_team
    and away_team.valid_from <= ge.perceived_at
    and (away_team.valid_until > ge.perceived_at or
         away_team.valid_until is null)
where away_score > home_score
  and hype >= 1.0