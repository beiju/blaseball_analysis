select num_tunnels / num_events as rate, qqq.team_id, nickname
from (select sum(1.0 / num_eligible) as num_events,
		sum((event_text like concat('%', player_name, ' entered the Tunnels%'))::int) as num_tunnels,
		team_id
	from (select unnest(event_text) as event_text, player_id, perceived_at, team_id, nickname, num_eligible
		from (select game_events.event_text,
			  team_roster.player_id,
			  game_events.perceived_at,
			  teams.team_id,
			  teams.nickname,
			  count(*) over (partition by game_events.id) as num_eligible
			from data.game_events
			left join data.games on game_events.game_id=games.game_id
			left join data.team_roster on team_roster.team_id=games.home_team
				and team_roster.tournament=-1
				and team_roster.position_type_id=1
				and team_roster.player_id <> games.winning_pitcher_id
				and team_roster.player_id <> games.losing_pitcher_id
				and team_roster.valid_from <= game_events.perceived_at
				and (team_roster.valid_until > game_events.perceived_at or team_roster.valid_until is null)
			inner join data.teams on team_roster.team_id=teams.team_id
				and teams.valid_from <= game_events.perceived_at
				and (teams.valid_until > game_events.perceived_at or teams.valid_until is null)
			inner join taxa.event_types on game_events.event_type=event_types.event_type
			where ((game_events.season=19 and game_events.day > 71) or game_events.season > 19)
				and plate_appearance>0
				and game_events.away_score >= 1) qq) q
	left join data.players on q.player_id=players.player_id
		and players.valid_from <= q.perceived_at
		and (players.valid_until > q.perceived_at or players.valid_until is null)
	group by team_id) qqq
left join data.teams on qqq.team_id=teams.team_id and teams.valid_until is null
order by num_tunnels / num_events desc
