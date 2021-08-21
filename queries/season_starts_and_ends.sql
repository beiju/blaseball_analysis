select
	season,
	min(perceived_at) as start,
	max(perceived_at) as end,
	(case when day < 99 then 'season' else 'postseason' end) as type
from data.game_events
where tournament=-1
group by season, day < 99
