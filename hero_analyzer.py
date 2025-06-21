import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

DATA_FILE = "hero_data.json"

# --- Colors for Dark/Light Mode ---
DARK_BG = "#22272e"
DARK_FG = "#f4f4f4"
LIGHT_BG = "#f7f8fa"
LIGHT_FG = "#22272e"

class HeroAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Overwatch 2 Hero Analyzer")
        self.root.geometry("950x600")
        self.dark_mode = True
        self.heroes = self.load_hero_data()
        self.filtered_heroes = self.heroes.copy()
        self.selected_hero = None

        # Team builder setup
        self.team_slots = {"Tank": [None], "DPS": [None, None], "Support": [None, None]}
        self.enemy_slots = {"Tank": [None], "DPS": [None, None], "Support": [None, None]}

        self.create_widgets()
        self.apply_theme()

    def load_hero_data(self):
        if not os.path.exists(DATA_FILE):
            messagebox.showerror("Error", f"Missing {DATA_FILE}")
            return []
        try:
            with open(DATA_FILE, 'r', encoding="utf-8") as file:
                data = json.load(file)
                return data.get("heroes", [])
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format in hero_data.json")
            return []

    def create_widgets(self):
        # --- Menu ---
        menubar = tk.Menu(self.root)
        menubar.add_command(label="Analyze", command=self.show_analyze)
        menubar.add_command(label="Team Builder", command=self.show_team_builder)
        menubar.add_command(label="Sources/About", command=self.show_sources)
        self.root.config(menu=menubar)

        # --- Top Bar (Dark Mode toggle + Search) ---
        topbar = tk.Frame(self.root, height=40)
        topbar.pack(side=tk.TOP, fill=tk.X)

        self.dark_btn = ttk.Button(topbar, text="🌙 Toggle Dark Mode", command=self.toggle_dark_mode)
        self.dark_btn.pack(side=tk.LEFT, padx=6)

        tk.Label(topbar, text="Search:").pack(side=tk.LEFT, padx=8)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(topbar, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind('<KeyRelease>', self.update_filter)

        # Role filters
        self.role_vars = {"Tank": tk.BooleanVar(value=True), "DPS": tk.BooleanVar(value=True), "Support": tk.BooleanVar(value=True)}
        for role in self.role_vars:
            c = ttk.Checkbutton(topbar, text=role, variable=self.role_vars[role], command=self.update_filter)
            c.pack(side=tk.LEFT, padx=3)

        # --- Main Frame ---
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.analyze_frame = None
        self.team_frame = None
        self.sources_frame = None

        self.show_analyze()

    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_analyze(self):
        self.clear_main()
        self.analyze_frame = tk.Frame(self.main_frame)
        self.analyze_frame.pack(fill=tk.BOTH, expand=True)

        # Hero list
        hero_list_frame = tk.Frame(self.analyze_frame)
        hero_list_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.hero_listbox = tk.Listbox(hero_list_frame, width=28)
        self.hero_listbox.pack(side=tk.LEFT, fill=tk.Y, padx=3, pady=6)
        self.hero_listbox.bind('<<ListboxSelect>>', self.on_hero_select)

        scrollbar = ttk.Scrollbar(hero_list_frame, orient=tk.VERTICAL, command=self.hero_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hero_listbox.config(yscrollcommand=scrollbar.set)

        self.update_hero_list()

        # Hero detail display
        self.detail_frame = tk.Frame(self.analyze_frame)
        self.detail_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)

        self.hero_title = tk.Label(self.detail_frame, text="Select a hero", font=("Arial", 18, "bold"))
        self.hero_title.pack(pady=5)

        self.stats_text = tk.Text(self.detail_frame, width=55, height=13, state=tk.DISABLED)
        self.stats_text.pack(pady=3)

        # Copy/export buttons
        copy_btn = ttk.Button(self.detail_frame, text="Copy Hero Info", command=self.copy_hero_info)
        copy_btn.pack(pady=1, side=tk.LEFT, anchor="w", padx=3)
        export_btn = ttk.Button(self.detail_frame, text="Export Hero JSON", command=self.export_hero_json)
        export_btn.pack(pady=1, side=tk.LEFT, anchor="w", padx=3)

    def show_team_builder(self):
        self.clear_main()
        self.team_frame = tk.Frame(self.main_frame)
        self.team_frame.pack(fill=tk.BOTH, expand=True)

        # Your team
        tk.Label(self.team_frame, text="Your Team", font=("Arial", 14, "bold")).pack(pady=2)
        self.team_selectors = {}
        for role, slots in self.team_slots.items():
            row = tk.Frame(self.team_frame)
            row.pack()
            tk.Label(row, text=role, width=8).pack(side=tk.LEFT)
            self.team_selectors[role] = []
            for i in range(len(slots)):
                cb = ttk.Combobox(row, state="readonly", width=17)
                cb['values'] = [h["name"] for h in self.heroes if h["role"] == role]
                cb.pack(side=tk.LEFT, padx=2)
                cb.bind("<<ComboboxSelected>>", lambda e, r=role, idx=i: self.on_team_select(r, idx))
                self.team_selectors[role].append(cb)

        # Enemy team
        tk.Label(self.team_frame, text="Enemy Team", font=("Arial", 14, "bold")).pack(pady=2)
        self.enemy_selectors = {}
        for role, slots in self.enemy_slots.items():
            row = tk.Frame(self.team_frame)
            row.pack()
            tk.Label(row, text=role, width=8).pack(side=tk.LEFT)
            self.enemy_selectors[role] = []
            for i in range(len(slots)):
                cb = ttk.Combobox(row, state="readonly", width=17)
                cb['values'] = [h["name"] for h in self.heroes if h["role"] == role]
                cb.pack(side=tk.LEFT, padx=2)
                cb.bind("<<ComboboxSelected>>", lambda e, r=role, idx=i: self.on_enemy_select(r, idx))
                self.enemy_selectors[role].append(cb)

        # Results panel
        self.matchup_text = tk.Text(self.team_frame, width=95, height=9, state=tk.DISABLED)
        self.matchup_text.pack(pady=8)

        # Update initial
        self.update_team_matchup()

    def show_sources(self):
        self.clear_main()
        self.sources_frame = tk.Frame(self.main_frame)
        self.sources_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        tk.Label(self.sources_frame, text="Sources & References", font=("Arial", 16, "bold")).pack(pady=8)
        sources = [
            ("Official Overwatch 2 site", "https://overwatch.blizzard.com/en-us/heroes"),
            ("Overwatch Wiki (Fandom)", "https://overwatch.fandom.com/wiki/Overwatch_Wiki"),
            ("Heropicker.io", "https://heropicker.io/overwatch"),
            ("Overbuff", "https://www.overbuff.com/heroes"),
            ("Esports.gg", "https://www.esports.gg/news/overwatch/"),
            ("India Today Gaming", "https://www.indiatodaygaming.com/story/overwatch-2-best-heroes-tier-list-2024-3715-2024-05-23"),
            ("CS2.gg Counter List", "https://www.cs2.gg/overwatch-2-counters")
        ]
        for name, url in sources:
            l = tk.Label(self.sources_frame, text=name, fg="blue", cursor="hand2", font=("Arial", 12, "underline"))
            l.pack(anchor="w")
            l.bind("<Button-1>", lambda e, link=url: os.system(f'start {link}' if os.name == 'nt' else f'open {link}'))

    def update_hero_list(self):
        self.hero_listbox.delete(0, tk.END)
        filtered = [h for h in self.filtered_heroes if self.role_vars[h["role"]].get()]
        for hero in filtered:
            self.hero_listbox.insert(tk.END, hero["name"])

    def update_filter(self, event=None):
        term = self.search_var.get().lower()
        self.filtered_heroes = [
            h for h in self.heroes
            if term in h["name"].lower() and self.role_vars[h["role"]].get()
        ]
        self.update_hero_list()

    def on_hero_select(self, event=None):
        idx = self.hero_listbox.curselection()
        if not idx:
            return
        hero_name = self.hero_listbox.get(idx[0])
        hero = next((h for h in self.heroes if h["name"] == hero_name), None)
        self.selected_hero = hero
        self.display_hero_details(hero)

    def display_hero_details(self, hero):
        self.hero_title.config(text=hero["name"])
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        lines = []
        lines.append(f"Role: {hero['role']}")
        lines.append(f"Health: {hero.get('health','N/A')}")
        lines.append(f"Damage: {hero.get('damage','N/A')}")
        if "abilities" in hero:
            lines.append("\nAbilities:")
            for ab in hero["abilities"]:
                lines.append(f"  • {ab['name']}: {ab['desc']} (Cooldown: {ab.get('cd','N/A')})")
        lines.append(f"\nStrengths: {', '.join(hero.get('strengths',[]))}")
        lines.append(f"Weaknesses: {', '.join(hero.get('weaknesses',[]))}")
        lines.append(f"Synergies: {', '.join(hero.get('synergies',[]))}")
        lines.append(f"Counters: {', '.join(hero.get('counters',[]))}")
        self.stats_text.insert(tk.END, "\n".join(lines))
        self.stats_text.config(state=tk.DISABLED)

    def copy_hero_info(self):
        if self.selected_hero:
            info = json.dumps(self.selected_hero, indent=2)
            self.root.clipboard_clear()
            self.root.clipboard_append(info)
            messagebox.showinfo("Copied!", f"Info for {self.selected_hero['name']} copied to clipboard.")

    def export_hero_json(self):
        if self.selected_hero:
            filename = f"{self.selected_hero['name'].replace(' ', '_')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.selected_hero, f, indent=2)
            messagebox.showinfo("Exported", f"Exported {filename}.")

    def on_team_select(self, role, idx):
        sel = self.team_selectors[role][idx].get()
        hero = next((h for h in self.heroes if h["name"] == sel), None)
        self.team_slots[role][idx] = hero
        self.update_team_matchup()

    def on_enemy_select(self, role, idx):
        sel = self.enemy_selectors[role][idx].get()
        hero = next((h for h in self.heroes if h["name"] == sel), None)
        self.enemy_slots[role][idx] = hero
        self.update_team_matchup()

    def update_team_matchup(self):
        # Gather picks
        team = [h for role in self.team_slots for h in self.team_slots[role] if h]
        enemy = [h for role in self.enemy_slots for h in self.enemy_slots[role] if h]
        result = []
        result.append("Your Team:\n  " + ", ".join([h["name"] for h in team]) if team else "Your Team: (empty)")
        result.append("Enemy Team:\n  " + ", ".join([h["name"] for h in enemy]) if enemy else "Enemy Team: (empty)")
        result.append("")

        # Synergy/counter analysis
        if team and enemy:
            result.append("Matchup Analysis:")
            # For each of your heroes, list who they counter in enemy
            for h in team:
                counters = set(h.get("counters", []))
                hits = [eh["name"] for eh in enemy if eh["name"] in counters]
                if hits:
                    result.append(f"  {h['name']} counters: {', '.join(hits)}")
            # For each enemy, list who they counter on your team
            for eh in enemy:
                counters = set(eh.get("counters", []))
                hits = [h["name"] for h in team if h["name"] in counters]
                if hits:
                    result.append(f"  Enemy {eh['name']} counters: {', '.join(hits)}")
        self.matchup_text.config(state=tk.NORMAL)
        self.matchup_text.delete("1.0", tk.END)
        self.matchup_text.insert(tk.END, "\n".join(result))
        self.matchup_text.config(state=tk.DISABLED)

    def apply_theme(self):
        bg, fg = (DARK_BG, DARK_FG) if self.dark_mode else (LIGHT_BG, LIGHT_FG)
        self.root.configure(bg=bg)
        self.main_frame.configure(bg=bg)
        for f in [self.analyze_frame, self.team_frame, self.sources_frame]:
            if f:
                f.configure(bg=bg)
        # Can extend to more widgets as needed

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.apply_theme()

if __name__ == "__main__":
    root = tk.Tk()
    app = HeroAnalyzerApp(root)
    root.mainloop()
