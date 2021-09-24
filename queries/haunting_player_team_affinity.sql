select q.*,
       batter.player_name    as batter_name,
       pitcher_team.nickname as pitcher_team_name
from (select count(*) as count, ge.batter_id, ge.pitcher_team_id
      from (select unnest(event_text) as txt, * from data.game_events) ge
      where ge.txt like '%Inhabiting%'
      group by ge.batter_id, ge.pitcher_team_id) q
         left join data.players batter
                   on batter.player_id = q.batter_id
                       and batter.valid_until IS NULL
         left join data.teams pitcher_team
                   on pitcher_team.id = (
                       select _t.id
		from data.teams _t
		where _t.team_id=q.pitcher_team_id
    and _t.nickname not like '%--%'
    and _t.nickname != 'team'
order by valid_until desc
    limit 1)
order by count desc
