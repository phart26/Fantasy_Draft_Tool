import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from Constants import constants as c
import Draft_Tracker

class DraftTrackerGUI:
    def setup_round_info(self):
        info_frame = ttk.Frame(self.root)
        info_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.round_label = ttk.Label(info_frame, text="")
        self.round_label.pack()
        self.update_round_info()

    def update_round_info(self):
        pick = Draft_Tracker.current_pick
        round_num = Draft_Tracker.get_round(pick)
        pick_in_round = Draft_Tracker.get_pick_in_round(pick)
        turn_msg = "✅ Your turn!" if Draft_Tracker.is_my_turn(pick) else ""
        self.round_label.config(text=f"Round {round_num}, Team {pick_in_round}, Overall Pick {pick} {turn_msg}")
    def __init__(self, root):
        self.root = root
        self.root.title("Fantasy Draft Tracker")
        self.prompt_for_position()
        self.setup_widgets()
        self.setup_round_info()
        self.refresh_recommendations()
        self.refresh_roster()

    def prompt_for_position(self):
        def set_position():
            try:
                pos = int(entry.get())
                if pos < 1 or pos > c.NUM_TEAMS:
                    raise ValueError
                Draft_Tracker.my_position = pos
                popup.destroy()
            except ValueError:
                messagebox.showerror("Input Error", f"Please enter a valid draft position (1-{c.NUM_TEAMS}).")

        popup = tk.Toplevel(self.root)
        popup.title("Draft Position")
        tk.Label(popup, text=f"Enter your draft position (1-{c.NUM_TEAMS}):").pack(padx=10, pady=10)
        entry = tk.Entry(popup)
        entry.pack(padx=10, pady=5)
        entry.focus()
        tk.Button(popup, text="OK", command=set_position).pack(pady=10)
        self.root.wait_window(popup)
    
    def clear_all_selections(self):
        # Clear selection in all tables
        self.rec_tree.selection_remove(self.rec_tree.selection())
        for tree in self.pos_trees.values():
            tree.selection_remove(tree.selection())

    def on_pos_tree_select(self, event):
        tree = event.widget
        selected = tree.selection()
        if selected:
            # Unselect all other rows in all tables
            self.clear_all_selections()
            # Select only the clicked row in this tree
            tree.selection_set(selected[0])
            values = tree.item(selected[0], 'values')
            if values:
                self.pick_entry.delete(0, tk.END)
                self.pick_entry.insert(0, values[0])

    def setup_widgets(self):
        # Main frame for left and right views
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        # Recommendations Frame (left)
        rec_frame = ttk.LabelFrame(main_frame, text="Top Recommendations")
        rec_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        columns = list(c.PLAYER_TABLE_CONFIG.keys())
        self.rec_tree = ttk.Treeview(rec_frame, columns=columns, show="headings")
        for col in columns:
            self.rec_tree.heading(col, text=col)
            self.rec_tree.column(col, width=c.PLAYER_TABLE_CONFIG.get(col, 50), anchor='center')
        self.rec_tree.pack(fill="x")
        self.rec_tree.bind("<ButtonRelease-1>", self.on_rec_tree_select)

        # Position Tables Frame (right)
        pos_frame = ttk.LabelFrame(main_frame, text="Top Players by Position")
        pos_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.pos_trees = {}
        pos_list = ["QB", "RB", "WR", "TE"]
        
        columns = list(c.PLAYER_TABLE_CONFIG.keys())
        for i, pos in enumerate(pos_list):
            n = 7 if pos == "WR" or pos == "RB" else 3
            tree = ttk.Treeview(pos_frame, columns=columns, show="headings", height=n)
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=c.PLAYER_TABLE_CONFIG.get(col, 50), anchor='center')
            tree.grid(row=i, column=0, sticky="ew", pady=2)
            ttk.Label(pos_frame, text=pos).grid(row=i, column=1, sticky="w")
            tree.bind("<ButtonRelease-1>", self.on_pos_tree_select)
            self.pos_trees[pos] = tree

        # Roster Frame (below recommendations)
        roster_frame = ttk.LabelFrame(main_frame, text="My Roster")
        roster_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        self.roster_tree = ttk.Treeview(roster_frame, columns=("Name", "Pos", "Team"), show="headings")
        roster_col_widths = {
            "Name": 90,
            "Pos": 40,
            "Team": 60
        }
        for col in ("Name", "Pos", "Team"):
            self.roster_tree.heading(col, text=col)
            self.roster_tree.column(col, width=roster_col_widths.get(col, 50), anchor='center')
        self.roster_tree.pack(fill="x")

        # Input Frame (below position tables)
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(input_frame, text="Enter drafted player:").grid(row=0, column=0)
        self.pick_entry_var = tk.StringVar()
        self.pick_entry = ttk.Entry(input_frame, textvariable=self.pick_entry_var, width=27)
        self.pick_entry.grid(row=0, column=1)
        self.pick_entry.bind('<KeyRelease>', self.on_pick_entry_search)
        self.pick_entry.bind('<FocusOut>', self.hide_pick_listbox)
        self.pick_listbox = None
        self.draft_me_btn = ttk.Button(input_frame, text="Draft for Me", command=self.draft_for_me)
        self.draft_other_btn = ttk.Button(input_frame, text="Other Team Drafted", command=self.draft_for_other)
        self.draft_me_btn.grid(row=0, column=2, padx=5)
        self.draft_other_btn.grid(row=0, column=3, padx=5)
        self.update_button_visibility()

    def on_pick_entry_search(self, event=None):
        value = self.pick_entry_var.get().lower()
        all_names = Draft_Tracker.get_available_player_names()
        filtered = [name for name in all_names if value in name.lower()]
        if self.pick_listbox:
            self.pick_listbox.destroy()
            self.pick_listbox = None
        if filtered and value:
            self.pick_listbox = tk.Listbox(self.pick_entry.master, height=min(8, len(filtered)), width=27)
            for name in filtered:
                self.pick_listbox.insert(tk.END, name)
            self.pick_listbox.grid(row=1, column=1, sticky="ew")
            self.pick_listbox.bind('<<ListboxSelect>>', self.on_pick_listbox_select)
            self.pick_listbox.lift()
        else:
            self.hide_pick_listbox()

    def on_pick_listbox_select(self, event=None):
        if self.pick_listbox:
            selection = self.pick_listbox.curselection()
            if selection:
                value = self.pick_listbox.get(selection[0])
                self.pick_entry_var.set(value)
            self.hide_pick_listbox()

    def hide_pick_listbox(self, event=None):
        if self.pick_listbox:
            self.pick_listbox.destroy()
            self.pick_listbox = None

    def on_rec_tree_select(self, event=None):
        selected = self.rec_tree.selection()
        if selected:
            # Unselect all other rows in all tables
            self.clear_all_selections()
            # Select only the clicked row in this tree
            self.rec_tree.selection_set(selected[0])
            values = self.rec_tree.item(selected[0], 'values')
            if values:
                self.pick_entry.delete(0, tk.END)
                self.pick_entry.insert(0, values[0])

    def update_button_visibility(self):
        if Draft_Tracker.is_my_turn(Draft_Tracker.current_pick):
            self.draft_me_btn.grid()
            self.draft_other_btn.grid_remove()
        else:
            self.draft_me_btn.grid_remove()
            self.draft_other_btn.grid()

    def refresh_recommendations(self):
        for row in self.rec_tree.get_children():
            self.rec_tree.delete(row)
        recs = Draft_Tracker.recommend_pick()
        for _, row in recs.iterrows():
            left = Draft_Tracker.players_left_in_tier(row[c.POS_COL], row[c.TIER_COL])
            self.rec_tree.insert('', 'end', values=(
                row[c.NAME_COL],
                row[c.POS_COL],
                row[c.TEAM_COL],
                row[c.WEIGHTED_SCORE_COL],
                row[c.TIER_COL],
                left,
                row.get(c.BYE_COL, ''),
                row.get('BYE_CONFLICT', '')
            ))

        # Update top players by position tables
        for pos, tree in self.pos_trees.items():
            for row_id in tree.get_children():
                tree.delete(row_id)
            n = 7 if pos == "WR" or pos == "RB" else 3
            pos_df = Draft_Tracker.top_n_by_position(pos, n)
            for _, prow in pos_df.iterrows():
                left = Draft_Tracker.players_left_in_tier(prow[c.POS_COL], prow[c.TIER_COL])
                bye_conflict = Draft_Tracker.bye_conflict_indicator(prow[c.POS_COL], prow[c.BYE_COL])
                tree.insert('', 'end', values=(
                    prow[c.NAME_COL],
                    prow[c.POS_COL],
                    prow[c.TEAM_COL],
                    prow[c.WEIGHTED_SCORE_COL],
                    prow[c.TIER_COL],
                    left,
                    prow.get(c.BYE_COL, ''),
                    bye_conflict
                ))

    def refresh_roster(self):
        for row in self.roster_tree.get_children():
            self.roster_tree.delete(row)
        for _, row in Draft_Tracker.my_roster_df.iterrows():
            self.roster_tree.insert('', 'end', values=(row[c.NAME_COL], row[c.POS_COL], row[c.TEAM_COL]))

    def draft_for_me(self):
        player = self.pick_entry_var.get().strip()
        if not player:
            messagebox.showwarning("Input Error", "Please enter a player name.")
            return
        Draft_Tracker.drafted_players.append(player)
        Draft_Tracker.my_team.append(player)
        Draft_Tracker.add_to_roster(player)
        Draft_Tracker.current_pick += 1
        self.pick_entry_var.set("")
        self.hide_pick_listbox()
        self.refresh_recommendations()
        self.refresh_roster()
        self.update_round_info()
        self.update_button_visibility()

    def draft_for_other(self):
        player = self.pick_entry_var.get().strip()
        if not player:
            messagebox.showwarning("Input Error", "Please enter a player name.")
            return
        Draft_Tracker.drafted_players.append(player)
        Draft_Tracker.current_pick += 1
        self.pick_entry_var.set("")
        self.hide_pick_listbox()
        self.refresh_recommendations()
        self.update_round_info()
        self.update_button_visibility()

if __name__ == "__main__":
    root = tk.Tk()
    app = DraftTrackerGUI(root)
    root.mainloop()
