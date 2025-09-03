import unittest
import pandas as pd
import numpy as np
from Constants import constants as c
import Draft_Tracker

class TestDraftTracker(unittest.TestCase):
    def setUp(self):
        # Example player data for testing
        self.player_data = pd.DataFrame({
            c.NAME_COL: ['Player A', 'Player B', 'Player C'],
            c.POS_COL: ['QB', 'RB', 'WR'],
            c.TEAM_COL: ['Team1', 'Team2', 'Team3'],
            c.WEIGHTED_SCORE_COL: [100, 90, 80],
            c.TIER_COL: [1, 1, 2],
            c.BYE_COL: [5, 6, 7]
        })
        Draft_Tracker.player_data = self.player_data
        Draft_Tracker.drafted_players = []
        Draft_Tracker.my_team = []
        Draft_Tracker.roster = {
            "QB": {"count": 0, "limit": 1},
            "RB": {"count": 0, "limit": 1},
            "WR": {"count": 0, "limit": 1},
            "TE": {"count": 0, "limit": 1}
        }

    def test_recommend_pick_returns_players(self):
        picks = Draft_Tracker.recommend_pick()
        self.assertEqual(len(picks), 3)
        self.assertIn(c.NAME_COL, picks.columns)

    def test_position_needed(self):
        self.assertTrue(Draft_Tracker.position_needed('QB'))
        Draft_Tracker.roster['QB']['count'] = 1
        self.assertFalse(Draft_Tracker.position_needed('QB'))

    def test_bye_penalty(self):
        Draft_Tracker.my_team = ['Player A']
        picks = Draft_Tracker.recommend_pick()
        # Player A should have a BYE_PENALTY of 1, others 0
        penalties = picks['BYE_PENALTY'].values
        self.assertIn(1, penalties)
        self.assertIn(0, penalties)

if __name__ == '__main__':
    unittest.main()
