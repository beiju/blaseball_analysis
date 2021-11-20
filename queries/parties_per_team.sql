select q.*, teams.nickname
from (select count(*), tr.team_id
      from (select unnest(event_text) as evt, *
            from data.game_events
            where array_to_string(event_text, ';') like '%is Partying!%') ge
               left join data.games on ge.game_id = games.game_id
               left join data.team_roster tr on (tr.team_id = games.home_team or
                                                 tr.team_id = games.away_team)
          and tr.position_type_id < 2 -- excludes shadows
          and tr.valid_from <= ge.perceived_at
          and (tr.valid_until > ge.perceived_at or tr.valid_until is null)
               left join data.players pl on pl.player_id = tr.player_id
          and pl.valid_from <= ge.perceived_at
          and (pl.valid_until > ge.perceived_at or pl.valid_until is null)
      where position(pl.player_name || ' is Partying' in ge.evt) > 0
      group by tr.team_id) q
         left join data.teams on teams.id = (
    select _t.id
		from data.teams _t
		where _t.team_id=q.team_id
    and _t.nickname not like '%--%'
    and _t.nickname != 'team'
order by valid_until desc
    limit 1
    )
order by q.count desc