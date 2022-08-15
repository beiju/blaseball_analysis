select player_name, q.*, three_runners + three_balls + runner_on_third as total
from (select
		pitcher_id,
		count(*) filter (where num_runners=3) as three_runners,
		count(*) filter (where total_balls=3) as three_balls,
		count(*) filter (where runner_on_third) as runner_on_third
	from (select game_event_id, count(*) as num_runners, sum(cast (geb.base_after_play=3 as int)) > 0 as runner_on_third from data.game_event_base_runners geb group by geb.game_event_id) geb
	inner join data.game_events ge on ge.id=geb.game_event_id
-- 	inner join data.player_modifications pm on pm.player_id=ge.pitcher_id
-- 		and pm.modification='TRIPLE_THREAT'
-- 		and pm.valid_from <= ge.perceived_at
-- 		and (pm.valid_until > ge.perceived_at or pm.valid_until is null)
	where ge.event_type='STRIKEOUT'
	group by pitcher_id) q
inner join data.players pl on pl.player_id=q.pitcher_id and pl.valid_until is null
order by three_runners + three_balls + runner_on_third desc