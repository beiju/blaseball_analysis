-- select distinct modification from data.stadium_modifications
-- relevant types are 'STOLEN_BASE', 'CAUGHT_STEALING'
-- relevant text to search is '%hops on the Grind Rail%', '%but lose their balance%'
select round(pl.overpowerment, 1) as attr,
	sum(array_length(pitches, 1)) as opportunitites,
	count(*) filter (where ge.event_type = 'STOLEN_BASE') as all_steals,
	count(*) filter (where ge.event_type = 'CAUGHT_STEALING') as all_caught,
	count(*) filter (where ge.event_type = 'STOLEN_BASE' and array_to_string(ge.event_text, '\n') like '%hops on the Grind Rail%') as grind_steals,
	count(*) filter (where ge.event_type = 'CAUGHT_STEALING' and array_to_string(ge.event_text, '\n') like '%hops on the Grind Rail%' and array_to_string(ge.event_text, '\n') like '%but lose their balance%') as grind_bail,
	count(*) filter (where ge.event_type = 'CAUGHT_STEALING' and array_to_string(ge.event_text, '\n') like '%hops on the Grind Rail%' and not array_to_string(ge.event_text, '\n') like '%but lose their balance%') as grind_caught
from data.game_events ge
inner join data.game_event_base_runners gebr
	on gebr.game_event_id = ge.id
inner join data.games_info_expanded_all game
	on game.game_id = ge.game_id
inner join data.players pl on gebr.runner_id=pl.player_id
	and pl.valid_from <= ge.perceived_at
	and (pl.valid_until > ge.perceived_at OR pl.valid_until IS NULL)

where base_before_play = 1
    -- this is the "Does the stadium have a grind rail" check
	and exists (select 1
			    from data.stadium_modifications sm
				where sm.stadium_id=game.stadium_id
					and modification='grind_rail_mod'
					and sm.valid_from < ge.perceived_at
					and (sm.valid_until > ge.perceived_at or sm.valid_until is null))
group by round(pl.overpowerment, 1)