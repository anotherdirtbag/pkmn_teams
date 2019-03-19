# Pokemon Team Combinations Calculator


### Description

Given an input csv of pokemon stats and some filter settings, this script searches for the best possible team combinations and exports the results as a csv.


[TLDR Gimme the Results](#results)

### Backstory

If you're at all like me, when you go to start a new pokemon game. You play through blindly until you've caught 7 pokemon. Then you need to go online and compare the base stats of all 7 so you can choose the best possible team of 6. 

Later on it gets more complicated when you want to choose a team that includes pokemon with high stats, a variety of types that don't share weakness, and the starter or some other favorite who you're determined to finish the game with regardless of their stats. 

Yada yada yada, I put the game down and made this script.



### Requirements

python 3

`pip3 install --user numpy sortedcontainers pandas scipy`



### Instructions

Load a csv into `unprocessed_stats_path` with at minimum these columns [Name, Type1, Type2, HP, Atk, Def, SpecialAtk, SpecialDef, Speed, Ability1, Ability2, HiddenAbility]
- If the generation doesn't support abilities, they will be ignored by the script, but the csv columns are still required.
- Also, if generation 1, make sure SpecialAtk = SpecialDef in the csv.
- Exclude pokemon with alternate form abilities like Darmanitan(Zen Mode) and Wishiwashi(Schooling). Use `seededchoices_names` if you insist on using them.
- Abilities that affect resistances and Truant are specifically handled in this script. Let me know if there are ways to handle other abilities. 

Define output filenames for `processed_stats_path` and `team_results_path`.

Define generation to use. This affects the inclusion of Dark/Steel/Fairy types and Abilities.

Define `seededchoices_names` with a list of pokemon to include in every set. This is for favorites and pokemon that defy stats like Wobbuffet.

Customize the team filtering settings and Score stat as you see fit. Take care to tune `pkmn_score_thresh` if you make changes.



### Customized Stats

To compare pokemon more easily, I attempted to boil down the 6 stats into one value that combines offensive and defensive prowess. I recommend customizing this however you see fit in the script.

```
MaxAttack = max(Atk, SpecialAtk)
```
I plan to rely on moves that utilize a pokemon strengths.

```
TotalDefense = sqrt( HP * min(Def, SpecialDef))
```
Only the minimum of Def and SpecialDef matters because any intelligent enemy will hit you where you're weakest.

```
Score = sqrt( MaxAttack * TotalDefense )
```
Using the geometric mean has a tendency to penalize cases where MaxAttack is dramatically larger than TotalDefense and visa versa so you'll hopefully end up with pokemon that balance attack and defense with high overall stats.

Alternately, it might be fun to create a glass cannon team using

```
SpeedRatio = 0.25
Score = (MaxAttack + Speed*SpeedRatio)/(1+SpeedRatio)
```

Or a tank team using

```
Score = TotalDefense
```



### Team Filtering

`pkmn_score_thresh`
This prevents pokemon with scores under this threshold from being considered in any teams. This has a dramatic effect on runtime, but needs care because the perfect fit to a strong team could be weaker than expected.

`team_4x_weakness_thresh`
Max number of 4x weaknesses on a team

`team_type_weakness_thresh`
Max number of pokemon allowed to be weak to a single type

`team_type_weakness_balance`
Balance after adding team weaknesses count and subtracting resistances count to a single type. 1 or 2 works well.


`team_AtkVsSpecial_balance`
Threshold to the number of pokemon that can favor attack vs special attack and visa versa. If attack and special are within ~15%, then they are considered equal. 



### Combinations

The math behind calculating all possible combinations is handled in the IndexedCombination class. 

```python
pkmnpool = list(range(total_pkmn_in_csv))[::-1]
combinator = IndexedCombination(6,pkmnpool)
for setindex in range(combinator.totalcombinations):
    fullset = combinator.get_nth_combination(setindex)
    if filtersetbyweakness(fullset) and filtersetbyattack(fullset):
        teamcompare = list(fullset) + teamstats(fullset)
        threadSortedResults.add(teamcompare)
```
This shows iterating through every possible team combination and adding those that pass the filtering settings to `threadSortedResults`.

Once `threadSortedResults` has reached `maxresultsize`, only teams with a combined score high enough will be added to the list. 

The combinations are sorted in what's called reverse co-lexographical order, where the pokemon are sorted by descending Score. This means a pokemon with an index of 75 has a higher Score then all pokemon with an index <75.

As such, we can guarantee that if team
75 74 73 72 71 50 has a score lower than the lowest scoring team in `threadSortedResults`. Then all teams with
75 74 73 72 71 and <50 will also not score high enough. IndexedCombination::skiptonextmaxima then skips to 74 73 72 70 69. 

For another example, if team 60 59 58 57 56 55 does not score high enough then no further combinations need to be evaluated.



### Other Settings

`maxresultsize`
The number of teams to save to `team_results_path`. Setting this too large will negatively affect speed.

`resumethreads`
When enabled, saves the current session to a .pickle file every print statement and loads that data on start if it exists.

`nprintsplit`
Controls how many iterations will run between printing to console and saving progress. For very long processing jobs, this will positively affect speed.


# Results

Using the default settings and the included csvs.

### Gen7 No Legendaries

```
"pokemonstats - gen7 no legendaries.unprocessed.csv"
assuming Hydreigon has Levitate
assuming Snorlax has Thick Fat
assuming Vikavolt has Levitate
187500601680 combinations using 229 pkmn
finished in 1154.4 seconds
```

1 | 2 | 3 | 4 | 5 | 6 | MaxAtk | TotalDef | TotalOffense | Score | Sum Team Weaknesses | Count Vulnerable Types | Count 4x Weaknesses
--|--|--|--|--|--|--|--|--|--|--|--|--
**Offensive** |--|--|--|--|--|--|--|--|--|--|--|--
Tyranitar | Dragonite | Metagross | Reuniclus | Vikavolt | Porygon-Z | 808 | 521.79 | 541.59 | 647.98 | 114.5 | 7 | 2
Tyranitar | Garchomp | Metagross | Vikavolt | Drampa | Chandelure | 824 | 511.57 | 559.15 | 647.43 | 113 | 8 | 2
Tyranitar | Salamence | Metagross | Reuniclus | Vikavolt | Porygon-Z | 809 | 515.99 | 554.24 | 644.84 | 114.5 | 7 | 2
Tyranitar | Metagross | Hydreigon | Reuniclus | Excadrill | Togekiss | 774 | 537.78 | 566.51 | 644.56 | 113.5 | 9 | 2
Tyranitar | Dragonite | Metagross | Drampa | Chandelure | Porygon-Z | 818 | 509.88 | 578.8 | 644.52 | 113.75 | 8 | 2
**Defensive** |--|--|--|--|--|--|--|--|--|--|--|--
Tyranitar | Escavalier | Reuniclus | Snorlax | Drampa | Togekiss | 759 | 549.83 | 428.75 | 644.5 | 113.25 | 6 | 2
Tyranitar | Metagross | Reuniclus | Snorlax | Vikavolt | Togekiss | 769 | 543.52 | 483.25 | 644.07 | 111.75 | 7 | 1
Tyranitar | Metagross | Reuniclus | Snorlax | Drampa | Togekiss | 759 | 548.95 | 474 | 643.94 | 113.75 | 7 | 1
Tyranitar | Metagross | Hydreigon | Snorlax | Vikavolt | Chandelure | 794 | 527.31 | 542.41 | 643.55 | 110.5 | 7 | 2
Tyranitar | Metagross | Snorlax | Vikavolt | Drampa | Togekiss | 779 | 534.11 | 491.72 | 642.36 | 110.75 | 5 | 1
Garchomp | Escavalier | Reuniclus | Snorlax | Vikavolt | Drampa | 780 | 531.77 | 434.47 | 641.47 | 109.25 | 6 | 2


### Gen7 All

```
"pokemonstats - gen7 all.unprocessed.csv"
assuming Giratina (O) has Levitate
1043156809240 combinations using 304 pkmn
finished in 34.1 seconds
```

1 | 2 | 3 | 4 | 5 | 6 | MaxAtk | TotalDef | TotalOffense | Score | Sum Team Weaknesses | Count Vulnerable Types | Count 4x Weaknesses
--|--|--|--|--|--|--|--|--|--|--|--|--
**Offensive** |--|--|--|--|--|--|--|--|--|--|--|--
Regigigas | Solgaleo | Mewtwo | Zekrom | Dialga | Yveltal | 882 | 627.5 | 729.52 | 742.97 | 105.75 | 5 | 0
Regigigas | Solgaleo | Mewtwo | Reshiram | Dialga | Yveltal | 882 | 627.5 | 729.52 | 742.97 | 105 | 4 | 0
Regigigas | Solgaleo | Mewtwo | Dialga | Rayquaza | Xerneas | 882 | 624.71 | 732.71 | 741.25 | 106.25 | 4 | 1
**Defensive** |--|--|--|--|--|--|--|--|--|--|--|--
Regigigas | Solgaleo | Zekrom | Dialga | Giratina (O) | Xerneas | 848 | 652.3 | 691.95 | 741.56 | 101.75 | 5 | 0
Regigigas | Solgaleo | Reshiram | Dialga | Giratina (O) | Yveltal | 848 | 652.3 | 691.95 | 741.56 | 102 | 7 | 0
Regigigas | Solgaleo | Reshiram | Dialga | Giratina (O) | Xerneas | 848 | 652.3 | 691.95 | 741.56 | 101 | 3 | 0
Regigigas | Solgaleo | Dialga | Giratina (O) | Arceus | Yveltal | 818 | 672.3 | 695.76 | 739.08 | 102 | 4 | 0
Regigigas | Solgaleo | Dialga | Giratina (O) | Arceus | Xerneas | 818 | 672.3 | 695.76 | 739.08 | 101 | 3 | 0





