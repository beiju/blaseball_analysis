select sum((modification is null)::int) as natural_events,
	   sum((modification is not null)::int) as unstable_events,
	   sum((incin and modification is null)::int) as natural_incins,
	   sum((incin and modification is not null)::int) as unstable_incins,
	   season_,
	   position_type_id
from (select EXISTS (
		SELECT -- can be empty
		FROM unnest(event_text) elem
		WHERE elem LIKE '%incinerated%'
			and (elem like concat('%hitter ', player_name, '!%')
				 or elem like concat('%pitcher ', player_name, '!%')
				 or elem like concat('%incinerated ', player_name, '!%'))
	  ) as incin,
	  games.season as season_,
		*
	from data.game_events
	left join data.games on game_events.game_id=games.game_id
	left join data.team_roster on (games.home_team=team_roster.team_id or games.away_team=team_roster.team_id)
		and (team_roster.position_type_id=0 or team_roster.position_type_id=1)
		and team_roster.valid_from <= game_events.perceived_at
		and (team_roster.valid_until > game_events.perceived_at or team_roster.valid_until is null)
	left join data.player_modifications on player_modifications.player_id=team_roster.player_id
		and modification='MARKED' /* unstable */
		and player_modifications.valid_from <= game_events.perceived_at
		and (player_modifications.valid_until > game_events.perceived_at or player_modifications.valid_until is null)
	left join data.players on players.player_id=team_roster.player_id
		and players.valid_from <= game_events.perceived_at
		and (players.valid_until > game_events.perceived_at or players.valid_until is null)
	where games.weather=7 /* solar eclipse */
		  ) q
group by season_, position_type_id
order by season_, position_type_id
