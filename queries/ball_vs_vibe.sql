select
	round(data.player_day_vibe(pitcher_id, day, perceived_at), 1) as vibe,
	count(*) as balls
from (select unnest(event_text) et, * from data.game_events) ge
-- very important that this is not inner join
left join data.player_mods_from_timestamp(perceived_at) pm on pm.player_id=ge.pitcher_id
	and pm.modification='FLINCH'
where (et like '%Ball.%' and not et like '%Foul Ball.%') -- (et like '%Strike, looking%') -- or (et like '%Ball.%' and not et like '%Foul Ball.%'))
	and pm.modification is null
	and season>11 and season < 18
group by round(data.player_day_vibe(pitcher_id, day, perceived_at), 1)