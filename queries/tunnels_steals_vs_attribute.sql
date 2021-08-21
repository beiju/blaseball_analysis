-- I never determined which attribute is the right one, if any

select --sum(1.0 / num_eligible) as num_events,
	--sum((event_text like concat('%', thief.player_name, ' entered the Tunnels%'))::int) as num_tunnels,
	victim.watchfulness,
	victim.player_name,
	thief.player_name,
	event_text
from (select unnest(event_text) as event_text, player_id, perceived_at, num_eligible, defending_pitcher
	from (select game_events.event_text,
		  team_roster.player_id,
		  game_events.perceived_at,
		  count(*) over (partition by game_events.id) as num_eligible,
		  (case when games.home_score > games.away_score then losing_pitcher_id else winning_pitcher_id end) as defending_pitcher
		from data.game_events
		left join data.games on game_events.game_id=games.game_id
		left join data.team_roster on team_roster.team_id=games.home_team
			and team_roster.tournament=-1
			and team_roster.position_type_id=1
			and team_roster.player_id <> games.winning_pitcher_id
			and team_roster.player_id <> games.losing_pitcher_id
			and team_roster.valid_from <= game_events.perceived_at
			and (team_roster.valid_until > game_events.perceived_at or team_roster.valid_until is null)
		inner join taxa.event_types on game_events.event_type=event_types.event_type
		where ((game_events.season=19 and game_events.day > 71) or game_events.season > 19)
			and plate_appearance>0) qq) q
left join data.players thief on q.player_id=thief.player_id
	and thief.valid_from <= q.perceived_at
	and (thief.valid_until > q.perceived_at or thief.valid_until is null)
left join data.players victim on q.defending_pitcher=victim.player_id
	and victim.valid_from <= q.perceived_at
	and (victim.valid_until > q.perceived_at or victim.valid_until is null)
where event_text like concat('%', thief.player_name, ' entered the Tunnels%')
order by victim.watchfulness
limit 30
