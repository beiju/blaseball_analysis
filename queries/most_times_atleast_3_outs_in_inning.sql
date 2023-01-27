-- the data here is questionable. holden is recorded as having 5 outs in an inning once
-- thanks to an out-of-order update. the top ranks should be correct-ish though
select qqq.*, pl.player_name
from (
	select count(*), player_id
	from (
		select game_id, inning, top_of_inning, player_id, sum(case when is_double_play then 2 else 1 end) as outs
		from (
			select ge.game_id, ge.inning, ge.top_of_inning, ge.is_double_play, ge.outs_on_play, coalesce(geb.runner_id, ge.batter_id) as player_id
			from data.game_events ge
			left join taxa.event_types et on et.event_type=ge.event_type
			left join data.game_event_base_runners geb on geb.game_event_id=ge.id
				and geb.was_caught_stealing
			where et.out>0
				and coalesce(geb.runner_id, ge.batter_id) is not null
				and coalesce(geb.runner_id, ge.batter_id) <> '') q
		group by game_id, inning, top_of_inning, player_id) qq
		where outs >= 3
		group by player_id) qqq
left join data.players pl on pl.player_id=qqq.player_id and valid_until is null
order by count desc, player_name
limit 200