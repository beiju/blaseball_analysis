select count(*),
       nickname,
       qq.team_id,
       array_agg(player_name) as player_names,
       array_agg(player_id)   as players
from (select q.*, player_name
      from (select distinct player_id, team_id
            from data.team_roster team_players
            where team_players.position_type_id < 2
              and team_players.player_id is not null
              and team_players.player_id != '' and team_players.player_id != 'UNKNOWN') q
               left join data.players pl on pl.player_id = q.player_id
          and pl.valid_until is null) qq
         left join data.teams team
                   on team.id = (
                       select _t.id
		from data.teams _t
		where _t.team_id=qq.team_id
    and _t.nickname not like '%--%'
    and _t.nickname != 'team'
order by valid_until desc
    limit 1)
group by qq.team_id, nickname
order by count (*) desc