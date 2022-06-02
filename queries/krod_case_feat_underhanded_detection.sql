-- select * from data.player_modifications where modification='UNDERHANDED'
-- select * from data.player_items where player_id='7a75d626-d4fd-474f-a862-473138d8c376'
select psps.*,
	data.pitching_rating(psps.player_id, (SELECT first_time FROM data.time_map WHERE DAY = 0 AND season = psps.season limit 1)),
	(exists (select 1
			 from data.player_modifications pm
			 where psps.player_id=pm.player_id
			and pm.modification='UNDERHANDED'
			and coalesce(pm.valid_from < (SELECT first_time FROM data.time_map WHERE DAY = 99 AND season = psps.season limit 1), true)
			and (pm.valid_until is null or pm.valid_until > (SELECT first_time FROM data.time_map WHERE DAY = 0 AND season = psps.season limit 1)))
	 or exists (select 1
			 from data.player_items pi
			 where psps.player_id=pi.player_id
			and pi.name ilike '%UNDERHANDED%'
			and coalesce(pi.valid_from < (SELECT first_time FROM data.time_map WHERE DAY = 0 AND season = (psps.season+1) limit 1), true)
			and (pi.valid_until is null or pi.valid_until > (SELECT first_time FROM data.time_map WHERE DAY = 0 AND season = psps.season limit 1)))
	) as underhanded,
	player_name='Kennedy Rodgers' as krod
from data.pitching_stats_player_season psps
where innings >= 50
order by underhanded, krod desc