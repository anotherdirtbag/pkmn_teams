# pkmn_teams
Pokemon Team Combinations Calculator

Given an input csv of pkmn stats and some filter settings, calculates the best possible team combinations.

requires python3
pip3 install --user numpy sortedcontainers pandas scipy

if numpy import errory try 'pip3 uninstall numpy' repeatedly until all versions are removed

Load a csv into unprocessed_stats_path with at minimum these columns ['Name','Type1','Type2', 'HP','Atk','Def','SpecialAtk','SpecialDef','Speed', 'Ability1','Ability2','HiddenAbility']
  - the Ability cols are still required, even if the generation doesnt support abilities. Just have empty cols.
  - Also, if gen 1, make SpecialAtk = SpecialDef in unprocessed_stats_path
  - Exclude pkmn with complicated abilites like Darmanitan(Zen Mode) and Wishiwashi(Schooling).
  - In addition to abilities that affect resistances, Truant is specifically handled in this calculator.

Define output filenames for processed_stats_path and team_results_path.

Define generation to use. This affects the inclusion of Dark/Steel/Fairy types and Abilities.

Define seededchoices_names with a list of pkmn to include in every set. This is for favorites and pkmn that defy stats like Wobbuffet


Read through the other user variables. The ones for filtering teams are the main way to customize results.

Customize calcStats if you disagree with how I "Score" the effectiveness of pkmn.

