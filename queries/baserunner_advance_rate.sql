select outs.*, outs.advanced / outs.advance_eligible::float as outs_rate, hits.*, hits.advanced_extra / hits.advance_extra_eligible::float as hits_rate, player_name, hits+walks as on_base
from (
	select runner_id,
		count(*) as advance_eligible,
		count(*) filter (where base_after_play > base_before_play) as advanced
		--array_agg(event_text[array_length(event_text, 1)]) as events
	from data.game_events ge
	inner join data.game_event_base_runners gebr on ge.id=gebr.game_event_id
	where ge.event_type='OUT'
		-- this is why you dont parse with string contains
		and not event_text[array_length(event_text, 1)] like '%draws a walk%'
		-- Select only plays where there is no runner on base (n+1) by the end of the play
		and not exists (select 1 from data.game_event_base_runners gebr_in where gebr_in.game_event_id=ge.id and gebr_in.base_before_play=gebr.base_before_play+1)
	group by runner_id
) outs
inner join (
	select runner_id,
		count(*) as advance_extra_eligible,
		count(*) filter (where base_after_play > base_before_play + et.total_bases) as advanced_extra
		--array_agg(event_text[array_length(event_text, 1)]) as events
	from data.game_events ge
	left join taxa.event_types et on et.event_type=ge.event_type
	inner join data.game_event_base_runners gebr on ge.id=gebr.game_event_id
	where ge.event_type in ('SINGLE', 'DOUBLE', 'TRIPLE', 'QUADRUPLE')
		-- Exclude plays where the normal amount of advancement scored them already
		and gebr.base_before_play+et.total_bases<(case when top_of_inning then away_base_count else home_base_count end)
		-- Select only plays where there is no runner on base (n+1) by the end of the play
		and not exists (select 1 from data.game_event_base_runners gebr_in where gebr_in.game_event_id=ge.id and gebr_in.base_before_play=gebr.base_before_play+et.total_bases+1)
	group by runner_id
) hits on hits.runner_id=outs.runner_id
left join data.batting_stats_player_lifetime bs on outs.runner_id=bs.player_id
where walks+hits>=300
order by outs.advanced / outs.advance_eligible::float desc
-- order by hits.advanced_extra / hits.advance_extra_eligible::float desc
