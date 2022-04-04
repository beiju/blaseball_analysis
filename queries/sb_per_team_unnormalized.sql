--select distinct event_type from data.game_events
select q.count, teams.nickname
from (select batter_team_id, count(*)
	from data.game_events
	where event_type='STOLEN_BASE'
	group by batter_team_id) q
left join data.teams on teams.id = (
    select _t.id
		from data.teams _t
		where _t.team_id=q.batter_team_id
    and _t.nickname not like '%--%'
    and _t.nickname != 'team'
order by valid_until desc
    limit 1
    )
union
-- i calculated this manually given the results of the above
select 3634 as count, 'Crabs (ascension-adjusted)' as nickname
order by count desc