select games,
       q.team_id,
       teams.nickname,
       q.player_id,
       players.player_name,
       position
from (
         select batter_id               as player_id,
                batter_team_id          as team_id,
                count(distinct game_id) as games,
                'batter' as position
         from data.game_events
         where batter_id is not null and batter_id <> ''
         group by batter_id, batter_team_id

         union

         select pitcher_id as player_id, pitcher_team_id as team_id, count (distinct game_id) as games, 'pitcher' as position
         from data.game_events
         where batter_id is not null and batter_id <> ''
         group by pitcher_id, pitcher_team_id
     ) q
         left join data.players on players.player_id = q.player_id and
                                   players.valid_until is null
         left join data.teams on teams.id = (
    select _t.id
		from data.teams _t
		where _t.team_id=q.team_id
    and _t.nickname not like '%--%'
    and _t.nickname != 'team'
order by valid_until desc
    limit 1
    )

order by games desc