select count, nickname, qq.team_id, player_names, players
from (select count(*),
             team_id,
             array_agg(player_name) as player_names,
             array_agg(player_id)   as players
      from (select distinct team_players.player_id, player_name, team_id
            from (select batter_id as player_id, batter_team_id as team_id
                  from data.game_events
                  union
                  select pitcher_id as player_id, pitcher_team_id as team_id
                  from data.game_events) team_players
                     left join data.players
                               on team_players.player_id = players.player_id
                                   and players.valid_until is null
            where team_players.player_id is not null
              and team_players.player_id != '' and team_players.player_id != 'UNKNOWN'
		  and exists (
			select from data.game_events e
			where (e.batter_id=team_players.player_id and e.batter_team_id='8d87c468-699a-47a8-b40d-cfb73a5660ad')
				or (e.pitcher_id=team_players.player_id and e.pitcher_team_id='8d87c468-699a-47a8-b40d-cfb73a5660ad'))) q
      group by team_id
      order by count(*) desc) qq
         left join data.teams team
                   on team.id = (
                       select _t.id
		from data.teams _t
		where _t.team_id=qq.team_id
    and _t.nickname not like '%--%'
    and _t.nickname != 'team'
order by valid_until desc
    limit 1)