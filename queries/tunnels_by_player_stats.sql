select *
from (select count(*) as total_plays,
             count(*)    filter (where entered_tunnels) as entered_tunnels, count(*) filter (where stole_run) as stole_run, count(*) filter (where stole_item) as stole_item, count(*) filter (where fled_elsewhere) as fled_elsewhere, count(*) filter (where nothing_interesting) as nothing_interesting, rotation_size,
             is_heist_expert,
             player_at_time_id
      from (select text like concat('%', player_name,
                                    ' entered the Tunnels...%')                                          as entered_tunnels,
                   text like concat('%', player_name,
                                    ' stole a Run from the%')                                            as stole_run,
                   text like concat('% caught their eye..._', player_name,
                                    ' stole%')                                                           as stole_item,
                   text like concat('%', player_name,
                                    ' fled Elsewhere to escape.%')                                       as fled_elsewhere,
                   text like concat('%', player_name,
                                    ' entered the Tunnels..._...but didn''t find anything interesting%') as nothing_interesting,
                   exists(select
                          from data.player_modifications pm
                          where pm.player_id = players.player_id
                            and pm.modification = 'HEIST_EXPERT'
                            and pm.valid_from <= perceived_at
                            and (pm.valid_until > perceived_at or
                                 pm.valid_until is null))                                                as is_heist_expert,
                   (select count(*)
                    from data.team_roster pr
                    where pr.team_id = events.pitcher_team_id
                      and pr.valid_from <= perceived_at
                      and (pr.valid_until > perceived_at or
                           pr.valid_until is null)
                      and pr.position_type_id = 1)                                                       as rotation_size,
                   players.id                                                                            as player_at_time_id
            from (select unnest(event_text) as text, *
                  from data.game_events) events
                     left join data.team_roster
                               on team_roster.team_id = pitcher_team_id
                                   and team_roster.valid_from <= perceived_at
                                   and
                                  (team_roster.valid_until > perceived_at or
                                   team_roster.valid_until is null)
                                   and position_type_id = 1 -- is a pitcher
                                   and team_roster.player_id <>
                                       pitcher_id -- is not pitching currently
                     left join data.players
                               on players.player_id = team_roster.player_id
                                   and players.valid_from <= perceived_at
                                   and (players.valid_until > perceived_at or
                                        players.valid_until is null)
            where (season > 19 or (season = 19 and day > 71))
              and text <> 'Play ball!'
              and text <> 'Game Over.'
              and not text like 'Top of % batting.'
              and event_index > 0 -- excludes A Blood Type, event horizion awaits, etc
              and event_type <> 'ELSEWHERE_ATBAT'
              and event_type <> 'SHELLED_ATBAT'
              and not text like '% batting for the %'
              and events.pitcher_id is not null) raw_events
      group by player_at_time_id, -- group by the DB record id, not player id, so there's a seperate group for all stat variations
               rotation_size,
               is_heist_expert) grouped_events
         left join data.players on players.id = player_at_time_id
--limit 10