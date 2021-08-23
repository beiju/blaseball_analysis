select game_id,
       count(*) as parties,
       (count(btm.modification) > 0) ::int + (count(ptm.modification) > 0)::int as teams_partying
from (select game_id,
             perceived_at,
             batter_team_id,
             pitcher_team_id,
             unnest(event_text) as evt
      from data.game_events) q
         left join data.team_modifications btm on btm.team_id = batter_team_id
    and btm.modification = 'PARTY_TIME'
    and btm.valid_from <= perceived_at
    and (btm.valid_until > perceived_at or btm.valid_until is null)
         left join data.team_modifications ptm on ptm.team_id = pitcher_team_id
    and ptm.modification = 'PARTY_TIME'
    and ptm.valid_from <= perceived_at
    and (ptm.valid_until > perceived_at or ptm.valid_until is null)
where evt like '%is Partying!%'
group by game_id