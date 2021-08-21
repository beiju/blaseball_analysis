select
	player_id,
	count(*) as num_oops,
	sum(slammed_it_down::int) as num_successful
from (select coalesce(next_in_roster, first_in_roster) as ooper, slammed_it_down, perceived_at
	from (select
		  	perceived_at,
			(select player_id
			 from data.team_roster team_roster_next
			 where team_roster_next.team_id=team_roster.team_id
				and position_type_id=0
				and team_roster_next.valid_from <= game_events.perceived_at
				and (team_roster_next.valid_until > game_events.perceived_at or team_roster_next.valid_until is null)
				and team_roster_next.position_id > team_roster.position_id
				order by position_id
				limit 1) as next_in_roster,
			(select player_id
			 from data.team_roster team_roster_next
			 where team_roster_next.team_id=team_roster.team_id
				and position_type_id=0
				and team_roster_next.valid_from <= game_events.perceived_at
				and (team_roster_next.valid_until > game_events.perceived_at or team_roster_next.valid_until is null)
				and team_roster_next.position_id=0) as first_in_roster,
			array_to_string(event_text, '; ') LIKE '%went up for the alley oop%' AS went_for_it,
			array_to_string(event_text, '; ') LIKE '%they slammed it down for%' AS slammed_it_down
		from data.game_events
		left join data.games on game_events.game_id=games.game_id
		inner join data.stadiums on stadiums.team_id=games.home_team
			and stadiums.valid_from <= game_events.perceived_at
			and (stadiums.valid_until > game_events.perceived_at OR stadiums.valid_until IS NULL)
			and stadiums.team_id<>'8d87c468-699a-47a8-b40d-cfb73a5660ad' -- necessary thanks to crabs big bucket fraud
		inner join data.stadium_modifications on stadiums.stadium_id=stadium_modifications.stadium_id
			and stadium_modifications.valid_from <= game_events.perceived_at
			and (stadium_modifications.valid_until > game_events.perceived_at OR stadium_modifications.valid_until IS NULL)
			and stadium_modifications.modification='hoops_mod'
		left join data.team_roster on game_events.batter_id=team_roster.player_id
			and team_roster.tournament=-1
			and team_roster.valid_from <= game_events.perceived_at
			and (team_roster.valid_until > game_events.perceived_at OR team_roster.valid_until IS NULL)
		where (event_type='HOME_RUN' or event_type='HOME_RUN_5')
			and array_to_string(event_text, '; ') LIKE '%went up for the alley oop%') q
	where went_for_it) qq
left join data.players on ooper=players.player_id
	and players.valid_from <= perceived_at
	and (players.valid_until > perceived_at OR players.valid_until IS NULL)
group by player_id
order by count(*) - sum(slammed_it_down::int) desc
