-- Written in support of Forrest Best's case for Hall of Fame
select hit.*, steal.*, pl.player_name, steals::float / on_base::float as steal_pct,
	case when on_base_no_fc = 0 then null else steals::float / on_base_no_fc::float end as steal_pct_no_fc,
	case when simple_on_base = 0 then null else steals::float / simple_on_base::float end as simple_steal_pct
from (select
	batter_id,
	count(*) as pa_approx,
	count(*) filter (where event_type in ('CHARM_WALK', 'DOUBLE', 'FIELDERS_CHOICE', 'HIT_BY_PITCH', 'INTENTIONAL_WALK', 'MIND_TRICK_WALK', 'QUADRUPLE', 'SINGLE', 'TRIPLE', 'WALK')) as on_base,
	count(*) filter (where event_type in ('CHARM_WALK', 'DOUBLE', 'HIT_BY_PITCH', 'INTENTIONAL_WALK', 'MIND_TRICK_WALK', 'QUADRUPLE', 'SINGLE', 'TRIPLE', 'WALK')) as on_base_no_fc,
	count(*) filter (where event_type in ('SINGLE', 'DOUBLE', 'TRIPLE', 'QUADRUPLE', 'WALK')) as simple_on_base
	from data.game_events ge
	where batter_id is not null and batter_id <> ''
	group by batter_id) hit
left join (select
		  runner_id,
		   count (*) filter (where was_base_stolen) as steals,
		   count (*) filter (where was_caught_stealing) as caught
		   from data.game_event_base_runners gebr
		   group by runner_id
		  ) steal on hit.batter_id=steal.runner_id
left join data.players pl on hit.batter_id = pl.player_id
	and pl.valid_until is null
where on_base > 0
order by steals::float / on_base::float desc