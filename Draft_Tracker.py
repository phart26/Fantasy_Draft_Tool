import pandas as pd
import numpy as np
from Constants import constants as c


# Data imports
player_data = pd.read_csv("./Data/Tiered_Player_Data.csv")

# Global Vars
my_position = 0
drafted_players = []
my_team = []
current_pick = 1

# DataFrame to track my roster
my_roster_df = pd.DataFrame(columns=[c.NAME_COL, c.POS_COL, c.TEAM_COL])


# Combined roster object: tracks both count and limit for each position
roster = {
    "QB": {"count": 0, "limit": 3},
    "RB": {"count": 0, "limit": 7},
    "WR": {"count": 0, "limit": 7},
    "TE": {"count": 0, "limit": 2}
}

def scarcity_alert(df, position, tier_cutoff=2):
    available = df[~df[c.NAME_COL].isin(drafted_players)]
    pos_available = available[available[c.POS_COL] == position]
    top_tier = pos_available[pos_available[c.TIER_COL] <= tier_cutoff]
    return len(top_tier) < 3


# DRAFT STATE TRACKING
def get_round(pick):
    return (pick - 1) // c.NUM_TEAMS + 1

def get_pick_in_round(pick):
    round_num = get_round(pick)
    if round_num % 2 == 1:
        return (pick - 1) % c.NUM_TEAMS + 1
    else:
        return c.NUM_TEAMS - ((pick - 1) % c.NUM_TEAMS)

def is_my_turn(pick):
    return get_pick_in_round(pick) == my_position


# RECOMMENDATION LOGIC

# Utility function to get all available player names (not drafted)
def get_available_player_names():
    available = player_data[~player_data[c.NAME_COL].str.lower().isin([p.lower() for p in drafted_players])]
    return sorted(available[c.NAME_COL].tolist())

# Utility function to get top N available players for a position
def top_n_by_position(pos, n):
    available = player_data[
        (player_data[c.POS_COL] == pos) &
        (~player_data[c.NAME_COL].str.lower().isin([p.lower() for p in drafted_players]))
    ].copy()
    available = available.sort_values(by=[c.TIER_COL, c.WEIGHTED_SCORE_COL], ascending=[True, False]).head(n)
    return available

# Utility function to get BYE conflict indicator for a player row
def bye_conflict_indicator(pos, bye):
    # Returns '⚠️' if any player in my_team at the same position has the same BYE week
    for player in my_team:
        row = player_data[player_data[c.NAME_COL].str.lower() == player.lower()]
        if not row.empty:
            player_pos = row[c.POS_COL].values[0]
            player_bye = row[c.BYE_COL].values[0]
            if player_pos == pos and player_bye == bye:
                return '⚠️'
    return ''

# Utility function to get number of players left in the same tier and position
def players_left_in_tier(pos, tier):
    return player_data[
        (player_data[c.POS_COL] == pos) &
        (player_data[c.TIER_COL] == tier) &
        (~player_data[c.NAME_COL].str.lower().isin([p.lower() for p in drafted_players]))
    ].shape[0]

def position_needed(pos):
    # Count total eligible slots for this position
    total_slots = roster[pos]["limit"] if pos in roster else 0
    return roster[pos]["count"] < total_slots

def recommend_pick():
    available = player_data[~player_data[c.NAME_COL].str.lower().isin([p.lower() for p in drafted_players])]
    # Filter by positions you still need
    available = available[available[c.POS_COL].apply(position_needed)]

    # Count BYE weeks for each position in my_team
    bye_counts = {}
    for player in my_team:
        row = player_data[player_data[c.NAME_COL].str.lower() == player.lower()]
        if not row.empty:
            pos = row[c.POS_COL].values[0]
            bye = row[c.BYE_COL].values[0]
            if pos not in bye_counts:
                bye_counts[pos] = {}
            bye_counts[pos][bye] = bye_counts[pos].get(bye, 0) + 1

    # Add a penalty column for BYE week conflicts
    def bye_penalty(row):
        pos = row[c.POS_COL]
        bye = row[c.BYE_COL]
        return bye_counts.get(pos, {}).get(bye, 0)

    available = available.copy()
    available['BYE_PENALTY'] = available.apply(bye_penalty, axis=1)

    # Sort by Tier and Weighted Score only
    available = available.sort_values(by=[c.TIER_COL, c.WEIGHTED_SCORE_COL], ascending=[True, False])

    # Add a column to indicate BYE week conflict
    available['BYE_CONFLICT'] = available['BYE_PENALTY'].apply(lambda x: '⚠️' if x > 0 else '')

    return available.head(7)

def add_to_roster(player_name):
    global my_roster_df
    # Find player info in df
    player_row = player_data[player_data[c.NAME_COL].str.lower() == player_name.lower()]
    if player_row.empty:
        print(f"Player {player_name} not found in data.")
        return
    pos = player_row[c.POS_COL].values[0]
    team = player_row[c.TEAM_COL].values[0] if c.TEAM_COL in player_row else np.nan

    my_roster_df = pd.concat([
        my_roster_df,
        pd.DataFrame({
            c.NAME_COL: [player_name],
            c.POS_COL: [pos],
            c.TEAM_COL: [team]
        })
    ], ignore_index=True)

    # Update positional count
    if pos in roster:
        roster[pos]["count"] += 1