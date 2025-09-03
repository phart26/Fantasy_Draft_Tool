import pandas as pd
import numpy as np
from Constants import constants as c

# Read both CSV files
projections = pd.read_csv('./Data/2025_Fantasy_Projections.csv')
ppg = pd.read_csv('./Data/PPG_Last3Years.csv')
bye_weeks = pd.read_csv('./Data/BYE_WEEKS.csv')

def assign_tiers(df, position, drop_threshold=10, drop_threshold_MAX= 40):
    pos_df = df[df[c.POS_COL] == position].sort_values(by=c.WEIGHTED_SCORE_COL, ascending=False)
    scores = pos_df[c.WEIGHTED_SCORE_COL].values
    indices = pos_df.index

    tier = 1
    first_score_in_tier = scores[0]
    df.at[indices[0], c.TIER_COL] = tier
    for i in range(1, len(scores)):
        # Increment tier if drop between adjacent scores is greater than threshold
        # OR if difference between first score in tier and current score is greater than drop_threshold_MAX
        if (scores[i-1] - scores[i] >= drop_threshold) or (first_score_in_tier - scores[i] >= drop_threshold_MAX):
            tier += 1
            first_score_in_tier = scores[i]
        df.at[indices[i], c.TIER_COL] = tier

# Merge on player name
df = pd.merge(
    projections,
    ppg.drop(columns=[c.TEAM_COL]),
    on=[c.NAME_COL, c.POS_COL],
    how="left"
)

# Add BYE WEEK
df = pd.merge(
    df,
    bye_weeks,
    on=[c.TEAM_COL],
    how="left"
)


# Calculate weighted score (customizable)
df[c.WEIGHTED_SCORE_COL] = np.where(
    df[c.AVG_PPG_PPR].isna(),
    df[c.PPR_PTS],
    df[c.PPR_PTS] * c.WEIGHT_PPR + (df[c.AVG_PPG_PPR]*16) * c.WEIGHT_AVG_PPG_PPR
)

for position in c.POSITIONS:
    assign_tiers(df, position)

# Save sorted DataFrame to CSV by position and tier
df[c.TIER_COL] = df[c.TIER_COL].astype(int)
df_sorted = df.sort_values(by=[c.POS_COL, c.WEIGHTED_SCORE_COL], ascending=[True, False])
df_sorted.to_csv('./Data/Tiered_Player_Data.csv', index=False)