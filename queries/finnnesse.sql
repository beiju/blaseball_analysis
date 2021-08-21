-- finnesse (of players with at least 5 games, per season during all pre-underhanded expansion era seasons)
select round(baserunners_stranded / runs_allowed, 3) as finnesse,
	round(runs_allowed, 1) as runs_allowed,
	baserunners_stranded,
	games,
	player_name,
	q.season + 1 as season_one_indexed
from (select count(*) as baserunners_stranded, pitcher_id, season
	from data.game_events
	inner join data.game_event_base_runners on game_events.id=game_event_base_runners.game_event_id
	where (outs_before_play + outs_on_play = 3)
	group by pitcher_id, season) q
left join (
	select sum(games) as games, sum(runs_allowed) as runs_allowed, player_id, player_name, season
	from data.pitching_stats_player_season
	group by player_id, player_name, season) stats
	on q.pitcher_id=stats.player_id and q.season=stats.season
where runs_allowed > 0 and games > 5 and q.season < 19 and q.season > 10
order by baserunners_stranded / runs_allowed desc
