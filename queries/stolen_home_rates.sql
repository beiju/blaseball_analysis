select q.*,
	num_thefts::float / num_eligible_events as steal_rate,
	num_caught::float / num_eligible_events as caught_rate,
	player_name,
	plate_appearances
from (
	select runner_id,
		count(*) filter (where plate_appearance>0 or was_base_stolen or was_caught_stealing) as num_eligible_events,
		count(*) filter (where was_base_stolen) as num_thefts,
		count(*) filter (where was_caught_stealing) as num_caught
-- 		array_agg(game_id)
	from data.game_events ge
	left join taxa.event_types et on ge.event_type=et.event_type
	inner join data.game_event_base_runners geb on ge.id=geb.game_event_id
		and geb.base_before_play=(case when ge.top_of_inning then away_base_count else home_base_count end)-1
	where runner_id is not null
-- 		and (plate_appearance=1 or was_base_stolen or was_caught_stealing)
	group by runner_id) q
left join data.batting_stats_player_lifetime bs on bs.player_id=q.runner_id
where num_eligible_events>0
-- 	and runner_id='f2a27a7e-bf04-4d31-86f5-16bfa3addbe7'
 	and plate_appearances > 500
order by num_thefts::float / num_eligible_events desc