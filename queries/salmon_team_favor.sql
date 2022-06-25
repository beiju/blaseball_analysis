select tm.nickname, q.*, q.runs_lost - q.runs_opponent_lost as net_run_loss
from (select 
		tm.team_id,
		sum(coalesce(substring(et from concat(' ([-\d.]+) of the ', tm.nickname, '''s')), '0')::numeric) as runs_lost,
		sum(coalesce(substring(et from concat(' ([-\d.]+) of the ', op.nickname, '''s')), '0')::numeric) as runs_opponent_lost
	from (select unnest(event_text) as et, * from data.game_events) ge
	left join data.teams tm on (tm.team_id=ge.batter_team_id or tm.team_id=ge.pitcher_team_id)
		and ge.perceived_at >= tm.valid_from
		and (ge.perceived_at < tm.valid_until or tm.valid_until is null)
	left join data.teams op on (op.team_id=ge.batter_team_id or op.team_id=ge.pitcher_team_id)
		and ge.perceived_at >= op.valid_from
		and (ge.perceived_at < op.valid_until or op.valid_until is null)
		and op.team_id<>tm.team_id
	where et like '%The Salmon swim upstream%'
	group by tm.team_id) q
left join data.teams tm on tm.team_id=q.team_id and tm.valid_until is null
order by q.runs_lost - q.runs_opponent_lost desc
