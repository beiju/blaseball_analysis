select substring(evt from '%out to #"%#".' for '#') as fielder_name,
       sum((evt like '%hit a ground out%')::int)    as ground_outs,
       sum((evt like '%hit a flyout%')::int)        as fly_outs
from (select unnest(event_text) as evt, * from data.game_events) as ge
where season = 10
  and pitcher_team_id = 'bfd38797-8404-4b38-8b82-341da28b1f83'
group by substring(evt from '%out to #"%#".' for '#')