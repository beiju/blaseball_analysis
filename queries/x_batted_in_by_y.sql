select q.*, bat.player_name as batter_name, run.player_name as runner_name
from (
	select batter_id, runner_id, count(*)
	from data.game_events ge
	inner join data.game_event_base_runners geb on geb.game_event_id=ge.id
	where geb.runs_scored <> 0
		and event_type='STOLEN_BASE'
		and event_type in ('HOME_RUN', 'SINGLE', 'SACRIFICE', 'DOUBLE', 'TRIPLE', 'FIELDERS_CHOICE', 'HOME_RUN_5', 'WALK', 'OUT', 'QUADRUPLE', 'CHARM_WALK', 'MIND_TRICK_WALK', 'HIT_BY_PITCH', 'SECRET_BASE_ENTER' )
		--and not (event_type in ('HOME_RUN', 'HOME_RUN_5') and batter_id=runner_id)
	group by batter_id, runner_id) q
left join data.players bat on bat.player_id=q.batter_id and bat.valid_until is null
left join data.players run on run.player_id=q.runner_id and run.valid_until is null
order by q.count desc