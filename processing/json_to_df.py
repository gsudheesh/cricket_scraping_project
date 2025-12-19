import os
import ujson
import pandas as pd
import glob
import re


    
# Function to process each JSON file and extract the data
def process_json_file(file_path, f):
    try:
        # Load the JSON data
        with open(file_path, 'r') as file:
            data = ujson.load(file)
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return pd.DataFrame()

    try:
        scorecard = data.get('scorecard', {})
        if not scorecard:
            return pd.DataFrame()


        bat_pos = {}
        innings = scorecard.get('content', {}).get('innings', [])
        for inning in innings:
            innsno=inning.get("inningNumber","")
            players=inning.get("inningBatsmen",[])
            bat_pos[innsno]={}
            for position,player in enumerate(players,start=1):
                player_id = player.get('player', {}).get('id')
                if player_id:
                    bat_pos[innsno][player_id] = position

        day_game = scorecard.get('match', {}).get('floodlit') in ['day', 'daynight']

        players = {}
        r = {}
        toss = {1: 'bat first', 2: 'bowl first'}
        bat = {}
        captains = {}
        results = {1: 'Result', 3: 'Tie', 5: 'No Result', None: None}
        home_team = None

        teams = scorecard.get('match', {}).get('teams', [])
        for pl in teams:
            try:
                team_info = pl.get('team', {})
                captain_info = pl.get('captain', {})
                team_name = team_info.get('longName', 'Unknown')
                captain_name = captain_info.get('name', 'Unknown')
                if pl.get('isHome', False):
                    home_team = team_name
                captains[team_name] = captain_name

                for innings in pl.get('inningNumbers', []):
                    bat[innings] = team_name
            except (KeyError, TypeError) as e:
                print(f"Error processing team or captain data: {e}")


        uniq = set()
        # Create player dictionary
        content = scorecard.get('content', {})
        teams = content.get('matchPlayers', {}).get('teamPlayers', [])
        for team in teams:
            try:
                team_id = team.get('team', {}).get('id')
                team_name = team.get('team', {}).get('longName', 'Unknown')
                r[team_id] = team_name
                uniq.add(team_name)
                for player in team.get('players', []):
                    try:
                        player_id = player.get('player', {}).get('id')
                        player_name = player.get('player', {}).get('name', 'Unknown')
                        dob = player.get('player', {}).get('dateOfBirth', None)
                        batting_styles = player.get('player', {}).get('battingStyles', ['Unknown'])
                        bowling_style = player.get('player', {}).get('bowlingStyles', ['Unknown'])

                        batting_style = batting_styles[0] if batting_styles else 'Unknown'

                        if player_id and player_name:
                            players[player_id] = [player_name, dob, batting_style, bowling_style]
                    except (KeyError, TypeError, IndexError) as e:
                        print(f"Error processing player data: {e}")
            except (KeyError, TypeError) as e:
                print(f"Error processing team data: {e}")

    except KeyError as e:
        print(f"Error in scorecard data: {e}")
        return pd.DataFrame()

    # Initialize detailed rows
    detailed_rows = []

    try:
        # Process the commentary data
        for inning in data.get('commentary', []):
            for ball in inning.get('comments', []):
                try:
                    inning_number = ball.get('inningNumber', 'Unknown')
                    batter_id = ball.get('batsmanPlayerId', None)
                    bowler_id = ball.get('bowlerPlayerId', None)
                    out_player = ball.get('outPlayerId', None)
                    batting_team = bat.get(inning_number, 'Unknown')
                    bowling_team = [i for i in uniq if i != batting_team][0] if uniq else 'Unknown'
                    

                    
                    predictions = ball.get('predictions', {})
                    score = predictions.get('score', None) if isinstance(predictions, dict) else None
                    win_probability = predictions.get('winProbability', None) if isinstance(predictions, dict) else None

                    

                    # Check for review data based on the inning and over
                    over = ball.get('oversActual', None)
                    

                    # Ensure dismissalText is a dictionary before accessing it
                    dismissal_text = ball.get('dismissalText', {})
                    if not isinstance(dismissal_text, dict):
                        dismissal_text = {}

                    match_player_awards = scorecard.get('content', {}).get('matchPlayerAwards', [])
                    player_of_match = match_player_awards[0].get('player', {}).get('name', None) if len(match_player_awards) > 0 else None
                    player_of_series = match_player_awards[1].get('player', {}).get('name', None) if len(match_player_awards) > 1 else None

                    detailed_row = {
                        'series_id': scorecard.get('match', {}).get('series', {}).get('objectId', None),
                        'series': scorecard.get('match', {}).get('series', {}).get('longName', None),
                        'match_type': scorecard.get('match', {}).get('format', None),
                        'year': scorecard.get('match', {}).get('series', {}).get('year', None),
                        'date': scorecard.get('match', {}).get('startDate', '').split('T')[0] if scorecard.get('match', {}).get('startDate') else None,
                        'venue': scorecard.get('match', {}).get('ground', {}).get('name', None),
                        'country': scorecard.get('match', {}).get('ground', {}).get('country', {}).get('name', None),
                        'match_id': scorecard.get('match', {}).get('objectId', None),
                        'match_no': scorecard.get('match', {}).get('title', None),
                        'batting_team': batting_team,
                        'bowling_team': bowling_team,
                        'innings': inning_number,
                        'over': ball.get('overNumber', None),
                        'ball': ball.get('ballNumber', None),
                        'ball_no': over,
                        'batsmanPlayerId': batter_id,
                        'bowlerPlayerId': bowler_id,
                        'batter': players.get(batter_id, ['Unknown'])[0],
                        'bowler': players.get(bowler_id, ['Unknown'])[0],
                        'totalRuns': ball.get('totalRuns', None),
                        'batruns': ball.get('batsmanRuns', None),
                        'balls_faced': 1 if not ball.get('wides') else 0,
                        'valid_ball': 1 if not (ball.get('wides') or ball.get('noballs')) else 0,
                        'isFour': ball.get('isFour', False),
                        'isSix': ball.get('isSix', False),
                        'isWicket': ball.get('isWicket', False),
                        'dismissalType': dismissal_text.get('short', None),
                        'byes': ball.get('byes', None),
                        'legbyes': ball.get('legbyes', None),
                        'wides': ball.get('wides', None),
                        'noballs': ball.get('noballs', None),
                        'penalties': ball.get('penalties', None),
                        'wagonX': ball.get('wagonX', None),
                        'wagonY': ball.get('wagonY', None),
                        'wagonZone': ball.get('wagonZone', None),
                        'pitchLine': ball.get('pitchLine', None),
                        'pitchLength': ball.get('pitchLength', None),
                        'shotType': ball.get('shotType', None),
                        'shotControl': 0 if ball.get('shotControl', None)==2 else 1,
                        'player_out': players.get(out_player, [None])[0],
                        'bat_hand': players.get(batter_id, ['Unknown', None, ''])[2].upper(),
                        'bowling_style': ",".join(players.get(bowler_id, ['Unknown', None, [], []])[3]),
                        'predictedScore': score,
                        'winProbabilty': win_probability,
                        'totalInningRuns': ball.get('totalInningRuns', None),
                        'totalInningWickets': ball.get('totalInningWickets', None),
                        'playerofmatch': player_of_match,
                        'playerofseries': player_of_series,
                        'winner': r.get(scorecard.get('match', {}).get('winnerTeamId', None)),
                        'toss_winner': r.get(scorecard.get('match', {}).get('tossWinnerTeamId', None)),
                        'toss_decision': toss.get(scorecard.get('match', {}).get('tossWinnerChoice', None)),
                        'isSuperOver': scorecard.get('match', {}).get('isSuperOver', False),
                        'result': results.get(scorecard.get('match', {}).get('resultStatus', None)),
                        'batting_captain': captains.get(batting_team, None),
                        'bowling_captain': captains.get(bowling_team, None),
                        'home_team': home_team,
                        'day_game': day_game,
                        'bat_pos': bat_pos.get(inning_number,{}).get(batter_id,None)
                    }
                    detailed_rows.append(detailed_row)
                except (KeyError, TypeError, IndexError) as e:
                    print(f"Error processing commentary data for ball: {ball}. Error: {e}")

    except (KeyError, TypeError, IndexError) as e:
        print(f"Error processing commentary data for file {file_path}: {e}")

    # Return the extracted data as a DataFrame
    return pd.DataFrame(detailed_rows)

# Main function to process all JSON files in the folder
def process_all_json_files(folder_path):
    all_dataframes = []

    # Find all JSON files in the folder
    json_files = glob.glob(os.path.join(folder_path, '*.json'))
    count = 1

    # Process each JSON file
    for json_file in json_files:
        print(count, json_file)
        with open(json_file, 'r') as file:
            data = ujson.load(file)

        scorecard = data.get('scorecard', {})
        if not scorecard:
            continue

        df = process_json_file(json_file, set())

        # Add batting position for each batter
        if not df.empty:
            all_dataframes.append(df)

        count += 1

    # Concatenate all DataFrames into a single DataFrame
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
    else:
        combined_df = pd.DataFrame()

    # Return the combined DataFrame
    return combined_df

# Example usage
folder_path ="C:/Users/sudhe/OneDrive/Desktop/rem_matches"
df = process_all_json_files(folder_path)

# Show the combined DataFrame
if not df.empty:
    df = df.sort_values(by=["date", "match_id", "innings", "over", "ball"])
    df['bowler_runs'] = df['totalRuns'] - df['byes'] - df['legbyes']
    df['bowler_wicket'] = ~df['dismissalType'].isin([None, 'obstruct field', 'retired hurt', 'retired not out', 'retired out', 'run out'])
    df['curr_batter_runs'] = df.groupby(['match_id', 'innings', 'batter'])['batruns'].cumsum()
    df['curr_batter_balls'] = df.groupby(['match_id', 'innings', 'batter'])['balls_faced'].cumsum()
else:
    print("No valid data extracted.")

df

print(df)

def save_df_to_csv(df, csv_path):
    # Check if the file already exists
    file_exists = os.path.isfile(csv_path)

    # Save the DataFrame
    df.to_csv(csv_path, mode='a', header=not file_exists, index=False)

folder_path = "../data/raw/rem_matches"
df = process_all_json_files(folder_path)

csv_path = "../data/processed/ball_by_ball_data.csv"
save_df_to_csv(df, csv_path)


