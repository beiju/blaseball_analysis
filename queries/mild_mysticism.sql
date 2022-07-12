select coalesce(mysticism, 0.5),
	count(*) as all_pitches,
	count(*) filter (where et like '%throws a Mild pitch%') as mild_pitches
from (select unnest(event_text) as et, * from data.game_events) ge
left join data.players pl on pl.player_id=ge.pitcher_id
	and (pl.valid_from <= ge.perceived_at)
	and (pl.valid_until > ge.perceived_at or pl.valid_until is null)
inner join data.player_modifications pm on pm.player_id=pl.player_id
	and (pm.valid_from <= ge.perceived_at)
	and (pm.valid_until > ge.perceived_at or pm.valid_until is null)
	and pm.modification='WILD'
left join data.games gm on gm.game_id=ge.game_id
left join data.stadiums st on st.team_id=gm.home_team
	and (st.valid_from <= ge.perceived_at)
	and (st.valid_until > ge.perceived_at or st.valid_until is null)
where et not like 'Top of %'
	and et not like 'Bottom of %'
	and et not like 'Play ball!'
	and et not like '% batting for the %'
group by coalesce(mysticism, 0.5)
having count(*) > 10000
order by coalesce(mysticism, 0.5)
