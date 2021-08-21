select
	COUNT(*) AS num_homers,
	SUM((array_to_string(event_text, '; ') LIKE '%The ball lands in a Big Bucket%')::int) AS num_buckets,
	round(moxie, 1) AS moxie
from data.game_events
left join data.games on game_events.game_id=games.game_id
inner join data.stadiums on stadiums.team_id=games.home_team
	and stadiums.valid_from <= game_events.perceived_at
	and (stadiums.valid_until > game_events.perceived_at OR stadiums.valid_until IS NULL)
	and stadiums.team_id<>'8d87c468-699a-47a8-b40d-cfb73a5660ad' -- necessary thanks to crabs big bucket fraud
inner join data.stadium_modifications on stadiums.stadium_id=stadium_modifications.stadium_id
	and stadium_modifications.valid_from <= game_events.perceived_at
	and (stadium_modifications.valid_until > game_events.perceived_at OR stadium_modifications.valid_until IS NULL)
	and stadium_modifications.modification='big_bucket_mod'
inner join data.players on game_events.batter_id=players.player_id
	and players.valid_from <= game_events.perceived_at
	and (players.valid_until > game_events.perceived_at OR players.valid_until IS NULL)
where event_type='HOME_RUN' or event_type='HOME_RUN_5'
group by round(moxie, 1)
--limit 10
