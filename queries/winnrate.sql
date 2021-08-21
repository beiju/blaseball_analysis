select winnie_wins_grouped.team, full_name, wins, losses, round(wins/(wins+losses+0.0), 3) as winnrate
from (select team, count(*) as wins
	from (select
			(case when home_score > away_score then home_team else away_team end) as team
		from data.games
		where losing_pitcher_id='f2a27a7e-bf04-4d31-86f5-16bfa3addbe7'
			and season > 11) winnie_wins
	group by team) winnie_wins_grouped
full outer join (select team, count(*) as losses
	from (select
			(case when home_score < away_score then home_team else away_team end) as team
		from data.games
		where winning_pitcher_id='f2a27a7e-bf04-4d31-86f5-16bfa3addbe7'
			and season > 11) winnie_losses
	group by team) winnie_losses_grouped on winnie_wins_grouped.team=winnie_losses_grouped.team
left join data.teams on winnie_wins_grouped.team=teams.team_id and teams.valid_until is null
order by wins/(wins+losses+0.0) desc
