-- teams with the most grand slams after Reload was given out
select qq.count, team.nickname, qq.bats
from (select batter_team_id as team_id, count(*), array_agg(batter.player_name) as bats
	from (select unnest(event_text) as txt, * from data.game_events) q
	  left join data.players batter on batter_id=player_id and batter.valid_until is null
	where season >= 22
		and (event_type='HOME_RUN' or event_type='HOME_RUN_5')
		and txt like '%grand slam%'
	group by batter_team_id
	order by count(*) desc) qq
left join data.teams team on team.id = (
   select _t.id
	from data.teams _t
	where _t.team_id=qq.team_id
		and _t.nickname not like '%--%'
		and _t.nickname != 'team'
	order by valid_until desc
		limit 1)
