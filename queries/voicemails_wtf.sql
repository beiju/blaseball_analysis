select
	nickname,
	sum((q.highest_score=0 and q.lowest_score=0)::int) as score_always_0,
	sum((q.highest_score=0)::int) as score_never_above_0,
	sum((games.home_score=0)::int) as score_ended_at_0
from (select game_id, max(home_score) as highest_score, min(home_score) as lowest_score from data.game_events
	where game_events.season=19
	group by game_id) q
left join data.games on games.game_id=q.game_id
left join data.teams on games.home_team=teams.team_id and teams.valid_until is null
group by team_id, nickname
order by sum((q.highest_score=0 and q.lowest_score=0)::int) desc
