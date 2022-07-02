-- See here for interpretation: (link to SIBR discord)
-- https://discord.com/channels/738107179294523402/875833188537208842/992855084880891986
select teams_in_party_time, avg(coalesce(num_parties, 0))
from (select distinct on (ge.game_id) num_parties,
		(select count(*)
			 from data.team_modifications tm
			 where (tm.team_id=gm.home_team OR tm.team_id=gm.away_team)
				and tm.modification='PARTY_TIME'
				and tm.valid_from <= ge.perceived_at
				and (tm.valid_until > ge.perceived_at or tm.valid_until is null)
			) as teams_in_party_time
	from data.games gm
	left join (
		select game_id, count(*) as num_parties
		from (select unnest(outcomes) as outcome, * from data.games) gm
		where outcome like '%is Partying%'
		group by game_id) parties on gm.game_id=parties.game_id
	inner join data.game_events ge on ge.game_id=gm.game_id
	order by ge.game_id, ge.perceived_at asc) q
group by teams_in_party_time