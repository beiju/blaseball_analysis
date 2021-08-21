-- season 23 pitcher performance stats by attribute

select stats.*,
	players.player_name,
	(walks + hits) / (outs / 3.0) as whip,
	hits / (outs / 27.0) as h9,
	home_runs / (outs / 27.0) as hr9,
	walks / (outs / 27.0) as bb9,
	strikeouts / (outs / 27.0) as so9,
	(case when walks=0 then 0 else strikeouts / (walks * 1.0) end) as so_bb
from (select pitcher_id, coldness, overpowerment, ruthlessness, shakespearianism, suppression, unthwackability,
		count(*) as game_events,
		count(*) filter (where event_types.out=1) as outs,
		count(*) filter (where game_events.event_type='STRIKEOUT') as strikeouts,
		count(*) filter (where game_events.event_type='WALK') as walks,
		count(*) filter (where event_types.hit=1) as hits,
		count(*) filter (where game_events.event_type='HOME_RUN' or game_events.event_type='HOME_RUN_5') as home_runs
	from data.game_events
	left join taxa.event_types on game_events.event_type=event_types.event_type
	left join data.players on game_events.pitcher_id=players.player_id
		and players.valid_from <= game_events.perceived_at
		and (players.valid_until > game_events.perceived_at or players.valid_until is NULL)
	where season=22 and pitcher_id is not null
	group by pitcher_id, coldness, overpowerment, ruthlessness, shakespearianism, suppression, unthwackability
) stats
-- Getting players outside the stats subquery so stats aren't grouped by name changes
left join data.players on stats.pitcher_id=players.player_id and players.valid_until is null
where outs > 0
