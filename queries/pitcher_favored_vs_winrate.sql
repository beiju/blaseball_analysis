with game_records as (select
		-- If home was favored and home won, or away was favored and away won, winning pitcher is favored pitcher
		(case when (home_odds > away_odds) = (home_score > away_score) then winning_pitcher_id else losing_pitcher_id end) as favored_pitcher_id,
		-- Reverse of above to get underdog pitcher
		(case when (home_odds > away_odds) = (home_score > away_score) then losing_pitcher_id else winning_pitcher_id end) as underdog_pitcher_id,
		winning_pitcher_id,
		losing_pitcher_id
	from data.games
	where winning_pitcher_id is not null
		and losing_pitcher_id is not null),
pitcher_records as (select
	player_name,
	(select count(*) from game_records where favored_pitcher_id=player_id) as times_favored,
	(select count(*) from game_records where underdog_pitcher_id=player_id) as times_underdog,
	(select count(*) from game_records where winning_pitcher_id=player_id) as times_won,
	(select count(*) from game_records where losing_pitcher_id=player_id) as times_lost
from data.players
where valid_until is null),
pitcher_ratios as (select
	*,
    times_won + times_lost as num_games,
	times_favored::float / (times_favored + times_underdog) as favored_ratio,
	times_won::float / (times_won + times_lost) as win_ratio
from pitcher_records
where times_won + times_lost > 0)
select *,
	win_ratio - favored_ratio as signed_ratio_difference,
	abs(win_ratio - favored_ratio) as ratio_difference
from pitcher_ratios
order by abs(favored_ratio - win_ratio) desc