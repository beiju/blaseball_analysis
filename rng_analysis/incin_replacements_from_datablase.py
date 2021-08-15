import pandas as pd
import re

"""
Query:

select distinct original_text, season 
from data.outcomes 
left join data.game_events on outcomes.game_event_id = game_events.id
where original_text like '%incinerated%'
	and original_text not like '%Fireproof%'
	and original_text not like '%incinerated the Hawai' -- cut off so i don't have to escape a '
	and original_text not like '%incinerated the Kansas City'

"""


def extract_info(event):
    return re.search('[rR]eplaced by (.+?)(:?$| The |\.)', event).group(1)


def main():
    incins = pd.read_csv('incinerations_events.csv')
    incins['name'] = incins['original_text'].transform(extract_info)
    incins['unstable'] = incins['original_text'].str.contains('The Instability')

    del incins['original_text']

    incins.to_csv('incinerations.csv', index=False)


if __name__ == '__main__':
    main()
