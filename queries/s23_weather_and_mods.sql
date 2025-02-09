-- note: turns out this query doesn't even answer the question it was designed for,
-- because weather renovations aren't stadium mods. i don't think weather renovations
-- are available in the datablase at all
with jazz_events as (
	select ge.game_id, ge.event_text
	from (select unnest(event_text) as event_text, game_id, season from data.game_events) ge
	where ge.event_text like '%A Riff Opened%'
), game_start_times as (
	select ge.game_id, min(ge.perceived_at) as start_time
	from data.game_events ge
	group by ge.game_id
)
select
	g.game_id,
	g.season,
	g.day,
	case
		when exists(select * from jazz_events je where je.game_id=g.game_id) then 'Jazz'
		else w.weather_text
	end as inital_weather,
	w.weather_text as final_weather,
	array(
		select hsm.modification
		from data.stadium_modifications hsm
		where
			hsm.stadium_id=hs.stadium_id and
			hsm.valid_from <= gst.start_time and
			(hsm.valid_until > gst.start_time or hsm.valid_until is null)
	) as home_stadium_mods,
	array(
		select asm.modification
		from data.stadium_modifications asm
		where
			asm.stadium_id=as_.stadium_id and
			asm.valid_from <= gst.start_time and
			(asm.valid_until > gst.start_time or asm.valid_until is null)
	) as home_stadium_mods
from data.games g
left join taxa.weather w on g.weather=w.weather_id
left join game_start_times gst on gst.game_id=g.game_id
left join data.stadiums hs on (
	hs.team_id=g.home_team and
	hs.valid_from <= gst.start_time and
	(hs.valid_until > gst.start_time or hs.valid_until is null)
)
left join data.stadiums as_ on (
	as_.team_id=g.away_team and
	as_.valid_from <= gst.start_time and
	(as_.valid_until > gst.start_time or as_.valid_until is null)
)
where g.season=22
order by g.season, g.day
