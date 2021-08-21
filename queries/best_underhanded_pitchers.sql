select *
from (select runs_groups.*,
		runs_by_hr/runs as proportion,
		player_name,
		rank() over (order by runs_by_hr/runs desc) as rank
	from (
		select pitcher_id,
			sum(runs_batted_in) AS runs,
			sum((case when event_type='HOME_RUN' or event_type='HOME_RUN_5' then runs_batted_in else 0 end)) as runs_by_hr
		from data.game_events
		where season=19
		group by pitcher_id) runs_groups
	left join data.players on pitcher_id=player_id and players.valid_until is null
	order by runs_by_hr/runs desc) ranked_pitchers
where player_name in ('Dunlap Figueroa',
'Adalberto Tosser',
'Mindy Kugel',
'Miguel James',
'King Weatherman',
'Winnie Hess',
'Juice Collins',
'Alexandria Rosales',
'Baldwin Breadwinner',
'Riley Firewall',
'Snyder Briggs',
'Nolanestophia Patterson',
'Patchwork Southwick',
'Ziwa Mueller', 'Wanda Schenn', 'Mindy Salad')
