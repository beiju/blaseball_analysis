select q.*
from (select season,
          day,
          teams.team_id,
          string_agg(distinct teams.full_name, '/') as full_name,
          avg (divinity) as divinity,
          avg (thwackability) as thwackability,
          avg (moxie) as moxie,
          avg (musclitude) as musclitude,
          avg (patheticism) as patheticism,
          avg (martyrdom) as martyrdom,
          avg (tragicness) as tragicness,
          avg (buoyancy) as buoyancy,
          avg (unthwackability) as unthwackability,
          avg (ruthlessness) as ruthlessness,
          avg (overpowerment) as overpowerment,
          avg (shakespearianism) as shakespearianism,
          avg (suppression) as suppression,
          avg (laserlikeness) as laserlikeness,
          avg (continuation) as continuation,
          avg (base_thirst) as base_thirst,
          avg (indulgence) as indulgence,
          avg (ground_friction) as ground_friction,
          avg (omniscience) as omniscience,
          avg (tenaciousness) as tenaciousness,
          avg (watchfulness) as watchfulness,
          avg (anticapitalism) as anticapitalism,
          avg (chasiness) as chasiness
      from (select min (perceived_at) as perceived_at, season, day from data.game_events where tournament=-1 group by season, day) times
          left join data.teams
      on teams.valid_from <= times.perceived_at
          and (teams.valid_until > times.perceived_at or teams.valid_until is null)
          left join data.team_roster on team_roster.team_id=teams.team_id
          and position_type_id<2
          and team_roster.valid_from <= times.perceived_at
          and (team_roster.valid_until > times.perceived_at or team_roster.valid_until is null)
          left join data.players on team_roster.player_id=players.player_id
          and players.valid_from <= times.perceived_at
          and (players.valid_until > times.perceived_at or players.valid_until is null)
      group by season, day, teams.team_id
      order by season, day) q
