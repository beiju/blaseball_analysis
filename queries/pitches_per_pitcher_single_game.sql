-- add "inning" to the group_by and both selects to get per-inning
select season + 1 as season_1, day + 1 as day_1, concat(at.nickname, ' @ ', ht.nickname), player_name, q.*
from (select
		sum(array_length(pitches, 1)) as pitches,
		game_id, pitcher_id
	from data.game_events ge
	where array_length(pitches, 1) is not null
	group by game_id, pitcher_id) q
left join data.games gm on gm.game_id=q.game_id
left join data.players pl on pl.player_id=q.pitcher_id and pl.valid_until is null
left join data.teams ht on ht.team_id=gm.home_team and ht.valid_until is null
left join data.teams at on at.team_id=gm.away_team and at.valid_until is null
order by q.pitches desc