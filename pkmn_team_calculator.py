#Authored by Christopher Wylie - 3/12/2019

#requires python3
#pip3 install --user numpy sortedcontainers pandas scipy
#if numpy import errory try 'pip3 uninstall numpy' repeatedly until all versions are removed

# Pokemon Team Combinations Calculator

# Load a csv into unprocessed_stats_path with at minimum these columns ['Name','Type1','Type2', 'HP','Atk','Def','SpecialAtk','SpecialDef','Speed', 'Ability1','Ability2','HiddenAbility']
#  - the Ability cols are still required, even if the generation doesnt support abilities. Just have empty cols.
#  - Also, if gen 1, make SpecialAtk = SpecialDef in unprocessed_stats_path
#  - Exclude pkmn with complicated abilites like Darmanitan(Zen Mode) and Wishiwashi(Schooling).
#  - In addition to abilities that affect resistances, Truant is specifically handled in this calculator.

# Define output filenames for processed_stats_path and team_results_path.
# Define generation to use. This affects the inclusion of Dark/Steel/Fairy types and Abilities.
# Define seededchoices_names with a list of pkmn to include in every set. This is for favorites and pkmn that defy stats like Wobbuffet

# Read through the other user variables. The ones for filtering teams are the main way to customize results.
# Customize calcStats if you disagree with how I "Score" the effectiveness of pkmn.



import os.path
import sys
import timeit
import csv
import pickle
import argparse
#import multiprocessing
#from concurrent import futures
from sortedcontainers import SortedList
from itertools import combinations
from pandas import Index
from scipy.special import comb
from numpy import array as nparray
from numpy import copy as npcopy
from math import sqrt


currentdir = os.path.dirname(sys.argv[0])

#*********** user variables ***********
generation = 6
seededchoices_names = set() #set(['Wobbuffet']) #names of pkmn to include in every set. must exactly match those in the input csv
# dramaticaly affects speed

# see expectedcsvheaders for required columns
unprocessed_stats_path = os.path.join(currentdir,'pokemonstats - soul silver catchable only no legendaries.unprocessed.csv')
processed_stats_path = os.path.join(currentdir,'pokemonstats - soul silver catchable only no legendaries.processed.csv')
team_results_path = 'teams - soul silver catchable only no legendaries.csv'

# unprocessed_stats_path = os.path.join(currentdir,'pokemonstats - gen7 no legendaries.unprocessed.csv')
# processed_stats_path = os.path.join(currentdir,'pokemonstats - gen7 no legendaries.processed.csv')
# team_results_path = 'teams - gen7 no legendaries.csv'

maxresultsize = 100 #the number of teams to save to team_results_path. This affects speed.


resumethreads = False #loads the previously processed csv. attempts to load .pickle file per thread to resume from saved data. 


pkmn_score_thresh = 83
# filter pkmn that have a score lower than this from all teams. this dramatically affects speed

# choosing higher filter thresholds affects speed
#see filtersetbyweakness
team_4x_weakness_thresh = 2 #max number of 4x weaknesses on a team
team_type_weakness_thresh = 3 #max number of pkmn allowed to be weak to a single type
team_type_weakness_balance = 1 #balance after adding team weaknesses count and subtracting resistances count to a single type

#see filtersetbyattack
team_AtkVsSpecial_balance = 3
#at most 3/6 of the pkmn can favor attack vs special attack
#if attack and special are within ~15%, then consider them equal

#see calcresistances. this is just for the results comparison, not filtering teams.
team_count_weak_types_thresh = 7.0
#count_weak_types: count of types the team has a total weakness value larger than team_count_weak_types_thresh

#these can be edited here to adjust how each team pkmns stats are scored and to calculate any extra values you might want
customelements = ['MaxAtk', 'TotalDef', 'TotalOffense']
def calcStats(pkmndata, csvheaders, ability):

    if ability == 'Truant':
        for i in ['Atk','SpecialAtk']:
            pkmndata[csvheaders[i]] = str(float(pkmndata[csvheaders[i]]) / 2)

    thispkmnstats = list( int(float(pkmndata[csvheaders[i]])) for i in ['HP','Atk','Def','SpecialAtk','SpecialDef','Speed'] )


    Total = sum(thispkmnstats)

    #customelements
    MaxAtk = max( list( int(float(pkmndata[csvheaders[i]])) for i in ['Atk','SpecialAtk'] ))
    TotalDef = sqrt( float( pkmndata[csvheaders['HP']]) * min( list( float(pkmndata[csvheaders[i]]) for i in ['Def','SpecialDef'] )) )
    TotalOffense = sqrt( float(MaxAtk) * float(pkmndata[csvheaders['Speed']]))
    Score = sqrt( float(MaxAtk) * TotalDef)

    thispkmnstats += [ Total, MaxAtk, TotalDef, TotalOffense, Score ]
    return thispkmnstats


#*********** command line ***********

# ap = argparse.ArgumentParser()
# ap.add_argument("-i", "--inputcsv", required=False, help="input csv", default=unprocessed_stats_path)
# ap.add_argument("-o", "--team_results_path", required=False, help="export results csv of final teams", default=team_results_path)
# ap.add_argument("-g", "--gen", required=False, help="generation. needed for resistance calcs", default=generation)
# ap.add_argument("-p", "--processedcsv", required=False, help="export processed pkmn data", default=processed_stats_path)
# ap.add_argument("-s", "--resultssize", required=False, help="number of teams in results csv", default=maxresultsize)
# ap.add_argument("-r", "--resumesupport", required=False, help="resume a previous run or save a .pickle", default=resumethreads)
# ap.add_argument("-s1", "--seed1", required=False, help="seeded choices included in every team", default='')
# ap.add_argument("-s2", "--seed2", required=False, help="seeded choices included in every team", default='')
# ap.add_argument("-s3", "--seed3", required=False, help="seeded choices included in every team", default='')
# ap.add_argument("-s4", "--seed4", required=False, help="seeded choices included in every team", default='')
# ap.add_argument("-s5", "--seed5", required=False, help="seeded choices included in every team", default='')
# args = vars(ap.parse_args())

# unprocessed_stats_path = args['inputcsv']
# team_results_path = args['team_results_path']
# generation = args['gen']
# processed_stats_path = args['processedcsv']
# maxresultsize = args['resultssize']
# resumethreads = args['resumesupport']

# if len(args['seed1']) > 0:
#     seededchoices_names += [args['seed1']]
# if len(args['seed2']) > 0:
#     seededchoices_names += [args['seed2']]
# if len(args['seed3']) > 0:
#     seededchoices_names += [args['seed3']]
# if len(args['seed4']) > 0:
#     seededchoices_names += [args['seed4']]
# if len(args['seed5']) > 0:
#     seededchoices_names += [args['seed5']]


#*********** global defs ***********
setsize = 6

abilitiesaffectingresistances = set( ['Dry Skin', 'Fluffy', 'Heatproof','Primordial Sea','Thick Fat','Water Bubble','Desolate Land','Water Absorb','Volt Absorb','Lightning Rod','Levitate', 'Motor Drive', 'Wonder Guard', 'Truant'])

alltypes =['Normal', 'Fire','Water','Electric','Grass','Ice','Fighting','Poison','Ground','Flying','Psychic','Bug','Rock','Ghost','Dragon']
if generation >= 2:
    alltypes += ['Dark','Steel']
if generation >= 6:
    alltypes += ['Fairy']

alltypesindex = dict()
i = 0
for header in alltypes:
    alltypesindex[header] = i
    i += 1

processedheaders = ['Name','Type1','Type2','Ability', 'HP','Atk','Def','SpecialAtk','SpecialDef','Speed','Total'] + customelements + ['Score'] + alltypes


processedcsv = [processedheaders]
pkmnstats = {}
statheaders = dict()
idx = 0
for i in range(processedheaders.index('HP'), len(processedheaders)):
    statheaders[ processedheaders[i] ] = idx
    idx += 1

#columns are attacking and rows are defending
#also rock paper scissors
if generation == 1:
    allresitances = nparray( [ [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1], \
        [1, 0.5, 2, 1, 0.5, 0.5, 1, 1, 2, 1, 1, 0.5, 2, 1, 1, 1, 0.5], \
        [1, 0.5, 0.5, 2, 2, 0.5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5], \
        [1, 1, 1, 0.5, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 1, 1, 1, 0.5], \
        [1, 2, 0.5, 0.5, 0.5, 2, 1, 2, 0.5, 2, 1, 2, 1, 1, 1, 1, 1], \
        [1, 2, 1, 1, 1, 0.5, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2], \
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0.5, 0.5, 1, 1, 0.5, 1], \
        [1, 1, 1, 1, 0.5, 1, 0.5, 0.5, 2, 1, 2, 0.5, 1, 1, 1, 1, 1], \
        [1, 1, 2, 0, 2, 2, 1, 0.5, 1, 1, 1, 1, 0.5, 1, 1, 1, 1], \
        [1, 1, 1, 2, 0.5, 2, 0.5, 1, 0, 1, 1, 0.5, 2, 1, 1, 1, 1], \
        [1, 1, 1, 1, 1, 1, 0.5, 1, 1, 1, 0.5, 2, 1, 2, 1, 2, 1], \
        [1, 2, 1, 1, 0.5, 1, 0.5, 1, 0.5, 2, 1, 1, 2, 1, 1, 1, 1], \
        [0.5, 0.5, 2, 1, 2, 1, 2, 0.5, 2, 0.5, 1, 1, 1, 1, 1, 1, 2], \
        [0, 1, 1, 1, 1, 1, 0, 0.5, 1, 1, 1, 0.5, 1, 2, 1, 2, 1], \
        [1, 0.5, 0.5, 0.5, 0.5, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1] ] )
elif generation < 6:
    allresitances = nparray( [ [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1], \
        [1, 0.5, 2, 1, 0.5, 0.5, 1, 1, 2, 1, 1, 0.5, 2, 1, 1, 1, 0.5], \
        [1, 0.5, 0.5, 2, 2, 0.5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5], \
        [1, 1, 1, 0.5, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 1, 1, 1, 0.5], \
        [1, 2, 0.5, 0.5, 0.5, 2, 1, 2, 0.5, 2, 1, 2, 1, 1, 1, 1, 1], \
        [1, 2, 1, 1, 1, 0.5, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2], \
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0.5, 0.5, 1, 1, 0.5, 1], \
        [1, 1, 1, 1, 0.5, 1, 0.5, 0.5, 2, 1, 2, 0.5, 1, 1, 1, 1, 1], \
        [1, 1, 2, 0, 2, 2, 1, 0.5, 1, 1, 1, 1, 0.5, 1, 1, 1, 1], \
        [1, 1, 1, 2, 0.5, 2, 0.5, 1, 0, 1, 1, 0.5, 2, 1, 1, 1, 1], \
        [1, 1, 1, 1, 1, 1, 0.5, 1, 1, 1, 0.5, 2, 1, 2, 1, 2, 1], \
        [1, 2, 1, 1, 0.5, 1, 0.5, 1, 0.5, 2, 1, 1, 2, 1, 1, 1, 1], \
        [0.5, 0.5, 2, 1, 2, 1, 2, 0.5, 2, 0.5, 1, 1, 1, 1, 1, 1, 2], \
        [0, 1, 1, 1, 1, 1, 0, 0.5, 1, 1, 1, 0.5, 1, 2, 1, 2, 1], \
        [1, 0.5, 0.5, 0.5, 0.5, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1], \
        [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0, 2, 1, 0.5, 1, 0.5, 1], \
        [0.5, 2, 1, 1, 0.5, 0.5, 2, 0, 2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5] ] )
else:
    allresitances = nparray( [ [ 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1], \
        [1, 0.5, 2, 1, 0.5, 0.5, 1, 1, 2, 1, 1, 0.5, 2, 1, 1, 1, 0.5, 0.5], \
        [1, 0.5, 0.5, 2, 2, 0.5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0.5, 1], \
        [1, 1, 1, 0.5, 1, 1, 1, 1, 2, 0.5, 1, 1, 1, 1, 1, 1, 0.5, 1], \
        [1, 2, 0.5, 0.5, 0.5, 2, 1, 2, 0.5, 2, 1, 2, 1, 1, 1, 1, 1, 1], \
        [1, 2, 1, 1, 1, 0.5, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1], \
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 0.5, 0.5, 1, 1, 0.5, 1, 2], \
        [1, 1, 1, 1, 0.5, 1, 0.5, 0.5, 2, 1, 2, 0.5, 1, 1, 1, 1, 1, 0.5], \
        [1, 1, 2, 0, 2, 2, 1, 0.5, 1, 1, 1, 1, 0.5, 1, 1, 1, 1, 1], \
        [1, 1, 1, 2, 0.5, 2, 0.5, 1, 0, 1, 1, 0.5, 2, 1, 1, 1, 1, 1], \
        [1, 1, 1, 1, 1, 1, 0.5, 1, 1, 1, 0.5, 2, 1, 2, 1, 2, 1, 1], \
        [1, 2, 1, 1, 0.5, 1, 0.5, 1, 0.5, 2, 1, 1, 2, 1, 1, 1, 1, 1], \
        [0.5, 0.5, 2, 1, 2, 1, 2, 0.5, 2, 0.5, 1, 1, 1, 1, 1, 1, 2, 1], \
        [0, 1, 1, 1, 1, 1, 0, 0.5, 1, 1, 1, 0.5, 1, 2, 1, 2, 1, 1], \
        [1, 0.5, 0.5, 0.5, 0.5, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2], \
        [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 0, 2, 1, 0.5, 1, 0.5, 1, 2], \
        [0.5, 2, 1, 1, 0.5, 0.5, 2, 0, 2, 0.5, 0.5, 0.5, 0.5, 1, 0.5, 1, 0.5, 0.5], \
        [1, 1, 1, 1, 1, 1, 0.5, 2, 1, 1, 1, 0.5, 1, 1, 0, 0.5, 2, 1] ])


seededchoices = [] # indexes of named pkmn in seededchoices_names
nprintsplit = 2000 #controls how many iterations will run between printing to console and saving progress.
debugcombinations = False

#*********** data preprocessing ***********

def calcpkmnresistances( thispkmncsvdata, csvheaders):
    global allresitances
    global abilitiesaffectingresistances
    global alltypesindex

    pkmnrestances = npcopy(allresitances[ alltypesindex[ thispkmncsvdata[csvheaders['Type1']] ]])
    #print(pkmnrestances)
    if thispkmncsvdata[csvheaders['Type2']] is not '':
        pkmnrestances2 = npcopy(allresitances[ alltypesindex[ thispkmncsvdata[csvheaders['Type2'] ]]])
        pkmnrestances *= pkmnrestances2
    
    if generation >= 3:
        pkmnabilities = set()

        abilityheaders = ['Ability1','Ability2']
        if generation >= 5:
            abilityheaders += ['HiddenAbility']

        for abileheader in abilityheaders:
            if thispkmncsvdata[csvheaders[abileheader]] is not '':
                pkmnabilities.add(thispkmncsvdata[csvheaders[abileheader]])

        possibleabilities = pkmnabilities.intersection(abilitiesaffectingresistances)

        if len(possibleabilities) > 0:
            ability = possibleabilities.pop()

            if len(possibleabilities) >= 1:
                print('assuming ' + str(thispkmncsvdata[csvheaders['Name']]) + ' has ' + str(ability) + ' and not ' + str(possibleabilities))
            else:
                print('assuming ' + str(thispkmncsvdata[csvheaders['Name']]) + ' has ' + str(ability))

            if ability == 'Dry Skin':
                pkmnrestances[ alltypesindex['Fire']] *= 1.25
                pkmnrestances[ alltypesindex['Water']] = 0
            elif ability == 'Thick Fat':
                pkmnrestances[ alltypesindex['Fire']] *= 0.5
                pkmnrestances[ alltypesindex['Ice']] *= 0.5
            elif ability == 'Fluffy':
                pkmnrestances[ alltypesindex['Fire']] *= 2
            elif ability == 'Heatproof' or ability == 'Water Bubble':
                pkmnrestances[ alltypesindex['Fire']] *= 0.5
            elif ability == 'Primordial Sea':
                pkmnrestances[ alltypesindex['Fire']] = 0
            elif ability == 'Desolate Land' or ability == 'Water Absorb':
                pkmnrestances[ alltypesindex['Water']] = 0
            elif ability == 'Volt Absorb' or ability == 'Lightning Rod' or ability == 'Motor Drive':
                pkmnrestances[ alltypesindex['Electric']] = 0
            elif ability == 'Levitate':
                pkmnrestances[ alltypesindex['Ground']] = 0
            elif ability == 'Wonder Guard':
                for thistype in pkmnrestances:
                    if thistype < 2:
                        thistype = 0
            elif ability != 'Truant':
                print('Error: no handler for ' + str(ability))
        else:
            ability = ''
    else:
        ability = ''
    return [ability, list(pkmnrestances)]


def preprocesscsvdata(validcsvpath, csvsavepath):
    #Load pkmn stats from csv data
    if not os.path.exists(validcsvpath):
        print('could not find ' + validcsvpath)
        sys.exit(1)
    global customelements
    global processedheaders

    scoreidx = processedheaders.index('Score')
    processedcsvdata = SortedList(key=lambda x: float(x[scoreidx])) #ascending order
    
    csvheaders = dict()
    csvdata = [[]]
    with open(validcsvpath,'r') as csvdatafile:
        csvreader = csv.reader(csvdatafile, delimiter=',')
        i = 0
        for row in csvreader:
            if i is 0:
                j = 0
                for col in row:
                    csvheaders[col] = j
                    j += 1
            else:
                csvdata.append(row)
            i += 1

    #expectedcsvheaders = ['Name','Type1','Type2', 'HP','Atk','Def','SpecialAtk','SpecialDef','Speed', 'Ability1','Ability2','HiddenAbility']
    
    
    for pkmndata in csvdata:
        processedpkmndata = []
        if len(pkmndata) is len(csvheaders): #this protects against csvdata[0] = []. not sure why this happens


            processedpkmndata += list( pkmndata[csvheaders[i]] for i in ['Name','Type1','Type2'])
            
            abilityandandres = calcpkmnresistances( pkmndata, csvheaders)
            ability = abilityandandres[0]
            processedpkmndata += [ability]
            
            thispkmnstats = calcStats(pkmndata, csvheaders, ability)
            processedpkmndata += list(map(str,thispkmnstats))

            processedpkmndata += list(map(str,abilityandandres[1])) #Resistances

            if float(thispkmnstats[-1]) < pkmn_score_thresh and not pkmndata[csvheaders['Name']] in seededchoices_names:
                continue

            processedcsvdata.add(processedpkmndata)
    
    if generation >= 3:
        print('To adjust ability assumptions, edit supported abilities by each pkmn in the unprocessed input csv') # or disable unwanted abilities via the command line')
    global pkmnstats
    global processedcsv
    processedcsv = [processedheaders]

    scoreidx = processedheaders.index('Score')

    with open(csvsavepath,'w') as csvdatafile:
        csvwriter = csv.writer(csvdatafile, delimiter=',')
        csvwriter.writerow(processedheaders)

        pkmnidx = 0
        hpidx = processedheaders.index('HP')
        for somerow in processedcsvdata.irange():
            
            processedcsv.append( somerow )
            csvwriter.writerow(somerow)

            for i in range(len(processedheaders) - hpidx):
                pkmnstats[pkmnidx, i] = float(somerow[i + hpidx])
            pkmnidx += 1



def loadprocessedcsvdata(validcsvpath):
    #Load pkmn stats from csv data
    if not os.path.exists(validcsvpath):
        print('could not find ' + validcsvpath)
        sys.exit(1)

    scoreidx = processedheaders.index('Score')
    processedcsvdata = SortedList(key=lambda x: float(x[scoreidx])) #ascending order
    
    csvheaders = dict()
    csvdata = [[]]
    with open(validcsvpath,'r') as csvdatafile:
        csvreader = csv.reader(csvdatafile, delimiter=',')
        i = 0
        for row in csvreader:
            if i is 0:
                j = 0
                for col in row:
                    csvheaders[col] = j
                    j += 1
            else:
                csvdata.append(row)
            i += 1

    for pkmndata in csvdata:
        if len(pkmndata) is len(csvheaders): #this protects against csvdata[0] = []. not sure why this happens
            
            if float(pkmndata[scoreidx]) < pkmn_score_thresh and not pkmndata[csvheaders['Name']] in seededchoices_names:
                continue
            
            processedcsvdata.add(pkmndata)
            if len(processedcsvdata) > maxresultsize:
                processedcsvdata.pop()

    global pkmnstats
    global processedcsv
    processedcsv = [processedheaders]

    pkmnidx = 0
    hpidx = processedheaders.index('HP')
    for somerow in processedcsvdata.irange():

        processedcsv.append( somerow )

        for i in range(len(processedheaders) - hpidx):
            pkmnstats[pkmnidx, i] = float(somerow[i + hpidx])
        pkmnidx += 1




#*********** team filters ***********

WeaknessRangeStart = statheaders['Normal']
WeaknessRangeEnd = statheaders[list(statheaders.keys())[-1]]+1 
#finds the last header in statheaders which should be 'Dragon', 'Steel', or 'Fairy'

def filtersetbyweakness(someset):
    # global team_type_weakness_balance
    # global team_type_weakness_thresh
    # global team_4x_weakness_thresh
    count4xweak = 0
    for type_idx in range(WeaknessRangeStart, WeaknessRangeEnd):
        typebalance = 0
        weakcount = 0
        for pkmn_idx in someset:
            resdata = int(2.0 * pkmnstats[pkmn_idx,type_idx] ) #used 2x since integer comparisions are faster and more predictable
            if resdata >= 4: # 2x
                weakcount += 1
                typebalance +=1
                if resdata >= 8: # 4x
                    count4xweak += 1
                    typebalance += 1
                if weakcount > team_type_weakness_thresh or count4xweak > team_4x_weakness_thresh:
                    return False
            #2 and 3 signify 1.0 to 1.5 which isnt a weakness or resistance
            elif resdata == 1: # 0.5x
                typebalance -= 1
            elif resdata == 0: # 0.25x or 0
                typebalance -= 2
        if typebalance > team_type_weakness_balance:
            return False
    return True




AtkIDX = statheaders['Atk']
SpecialAttackIDX = statheaders['SpecialAtk']
def filtersetbyattack(someset):
    #global team_AtkVsSpecial_balance
    teamattack = 0
    teamspecial = 0
    for pkmn_idx in someset:
        atkratio = pkmnstats[pkmn_idx,AtkIDX] / pkmnstats[pkmn_idx,SpecialAttackIDX]
        if atkratio >= 1.18:
            teamattack += 1
        elif atkratio < 0.85:
            teamspecial += 1
    if teamattack > team_AtkVsSpecial_balance or teamspecial > team_AtkVsSpecial_balance:
        return False
    return True




def calcresistances(someset):
    global team_count_weak_types_thresh
    sum_weaknesses = 0
    count_weak_types = 0
    count4xweak = 0
    for pkmn_idx in someset:
        for pkmn_res in [pkmnstats[pkmn_idx,i] for i in range(WeaknessRangeStart,WeaknessRangeEnd)]:
            sum_weaknesses += pkmn_res
    for type_idx in range(WeaknessRangeStart, WeaknessRangeEnd):
        team_res = 0.0
        for pkmn_idx in someset:
            pkmn_res = pkmnstats[pkmn_idx,type_idx]
            #sum_weaknesses += pkmn_res
            team_res += pkmn_res
            if pkmn_res >= 4:
                count4xweak += 1
        if team_res >= team_count_weak_types_thresh:
            count_weak_types += 1
    return [sum_weaknesses, count_weak_types, count4xweak]
teamresistancesheaders = ['Sum Team Weaknesses', 'Count Vulnerable Types', 'Count 4x Weaknesses']
#sum_weaknesses: just adding all type weakness 0-4 per type per pkmn
#count_weak_types: count of types the team is vulnerable to. Team type weakness value larger than team_count_weak_types_thresh




TeamStatsStart = statheaders[customelements[0]]
TeamStatsEnd = statheaders['Score'] + 1
teamstatsheaders = customelements + ['Score']

def teamstats(someset):
    totalstats = [0]*(TeamStatsEnd - TeamStatsStart)
    for pkmn_idx in someset:
        for statidx in range(TeamStatsStart, TeamStatsEnd):
            totalstats[statidx - TeamStatsStart] += pkmnstats[pkmn_idx,statidx]
    return totalstats + calcresistances(someset)




#*********** combinations calculator ***********


#TheCombinator = IndexedCombination( 6, range(len(csvdata) - 1))
#TheCombinator.get_nth_combination(someindex)
class IndexedCombination:
    def __init__(self, _setsize, _poolvalues):
        #globals for poolsizeth_combination
        self.setsize = _setsize
        self.poolvals = Index(_poolvalues)
        self.poolsize = len(self.poolvals)
        if self.setsize < 0 or self.setsize > self.poolsize:
            raise ValueError
        self.totalcombinations = 1
        fast_k = min(self.setsize, self.poolsize - self.setsize)
        for i in range(1, fast_k + 1):
            self.totalcombinations = self.totalcombinations * (self.poolsize - fast_k + i) // i
        
        #fill the nCr cache
        self.choose_cache = {}
        n = self.poolsize
        k = self.setsize
        for i in range(k + 1):
            for j in range(n + 1):
                if n - j >= k - i:
                    self.choose_cache[n - j,k - i] = comb(n - j,k - i, exact=True)
        if debugcombinations:
            print('testnth = ' + str(self.testnth()))

    def get_nth_combination(self,index):
        n = self.poolsize
        r = self.setsize
        c = self.totalcombinations
        #if index < 0 or index >= c:
        #    raise IndexError
        result = []
        while r:
            c, n, r = c*r//n, n-1, r-1
            while index >= c:
                index -= c
                c, n = c*(n-r)//n, n-1
            result.append(self.poolvals[-1 - n])
        return tuple(result)

    def get_n_from_combination(self,someset):
        n = self.poolsize
        k = self.setsize
        index = 0
        j = 0
        for i in range(k):
            #this poolvals business can be avoided if someset is simply an index into parentset_pool instead of the original csv!!!!
            #setidx = self.poolvals.index(someset[i]) #if no pandas. the speed improvement will grow relative to poolsize.
            setidx = n - someset[i] - 1 
            for j in range(j + 1, setidx + 1):
                index += self.choose_cache[n - j, k - i - 1]
            j += 1
        return index

    def skiptonextmaxima(self, fullset): #this assumes that fullset references an unbroken range of integers. this will break if that is not the case
        nextset = list(fullset)[::-1] #reverse to change from BE to LE.
        _setsize = len(fullset)
        x = 1
        while x < _setsize:
            if nextset[x - 1] + 1 == nextset[x]:
                x += 1
            else:
                break

        if x >= setsize - len(seededchoices): #already a major maxima. skip all further sets
            return []
        
        nextset[x] -= 1
        for i in list(range(x))[::-1]:
            nextset[i] = nextset[i + 1] - 1
            
        return nextset[::-1]

    #just used to test whether nth_combination from the internet actually works
    def testnth(self):
        n = 0
        _setsize = self.setsize
        mainset = self.poolvals
        for someset in combinations(mainset, _setsize):
            nthset = self.get_nth_combination(n)
            n2 = self.get_n_from_combination(nthset)
            #print(str(n) + ': ' + str(someset) + ' vs ' + str(n2) + ': ' + str(nthset))
            if n != n2:
                return False
            for x in range(_setsize):
                if someset[x] != nthset[x]:
                    return False
            n += 1
        return True
if debugcombinations:
    pool = list(range(76))[::-1]
    setcombination = IndexedCombination(3, pool)
    exit()




#*********** threading ***********
#cnvert this to before and after optimization
#remove old printing stuff

def parentpool_to_csvdata(map_subpool_to_csv, subset):
    return [map_subpool_to_csv[subpoolidx] for subpoolidx in subset]

#per thread...
def processthread(trange):

    teamstatsScoreidx = teamstatsheaders.index('Score')
    sortedScoreidx = setsize + teamstatsScoreidx
    threadSortedResults = SortedList(key=lambda x: -x[sortedScoreidx])
     #todo check this index
    minScore = 0

    istart = trange[0]
    isize = trange[1] - trange[0]
    iend = trange[1]
    doprinting = trange[2]
    logfilepath = os.path.join(currentdir, trange[3])
    resumeset = istart
    if resumethreads and os.path.exists(logfilepath):
        with open(logfilepath, 'rb') as logfile:
            resumeset = pickle.load(logfile)
            if resumeset < istart or resumeset >= iend - 1:
                print('cant resume set ' + logfilepath)
                resumeset = istart
            else:
                print( 'resuming ' + os.path.basename(logfilepath) + ' from ' + str(resumeset))
                for someset in pickle.load(logfile):
                    threadSortedResults.add(someset)


    map_subpool_to_csv = list(range(len(processedcsv) - 1)) #indexes of all the pokemon in csvdata and pkmnstats
    #reverse to generate 'reverse colexigraphical' order

    for somesetidx in seededchoices: #remove the seeded choices if any
        map_subpool_to_csv.remove(somesetidx)

    subsetpool = list(range(len(processedcsv) - 1 - len(seededchoices)))[::-1] #make a separate index. ex: pkmnstats[ 1 + map_subpool_to_csv[setidx]]
    if len(map_subpool_to_csv) != len(subsetpool):
        print('error in map_subpool_to_csv')
        exit()

    subsetsize = setsize - len(seededchoices)

    threadcombinator = IndexedCombination( subsetsize, subsetpool)
    threadtimerstart = timeit.default_timer()
    skippedrange = 0
    #for setindex in range( resumeset, iend):
    setindex = resumeset
    while setindex < iend:
        for iprintsplit in range(nprintsplit):
            parentset = threadcombinator.get_nth_combination(setindex)

            if len(seededchoices) > 0:
                fullset = seededchoices + parentpool_to_csvdata(map_subpool_to_csv,parentset)
            else:
                fullset = parentpool_to_csvdata(map_subpool_to_csv,parentset)
            
            if len(threadSortedResults) < maxresultsize:
                if filtersetbyweakness(fullset) and filtersetbyattack(fullset):
                    teamcompare = list(fullset) + teamstats(fullset)
                    threadSortedResults.add(teamcompare)
            else:
                teamcompare = list(fullset) + teamstats(fullset)
                if teamcompare[sortedScoreidx] > minScore: #todo check this index
                    if filtersetbyweakness(fullset) and filtersetbyattack(fullset):
                        threadSortedResults.add(teamcompare)
                        threadSortedResults.pop()
                        minScore = threadSortedResults[-1][sortedScoreidx]
                else:
                    #skip to next combination where its possible for the stats to be high enough.
                    nextset = threadcombinator.skiptonextmaxima(parentset)
                    if len(nextset) == 0:
                        new_setindex = iend
                    else:
                        new_setindex = threadcombinator.get_n_from_combination(nextset) - 1
                    skippedrange += (new_setindex + 1 - setindex)
                    setindex = new_setindex
            setindex += 1
            if setindex >= iend:
                break
        
        if doprinting:
            threadtimernow = timeit.default_timer()
            combinationspersecond = (setindex - istart)/(threadtimernow - threadtimerstart)
            print("{0:.6f}".format((setindex - istart)/isize * 100), '%' + ' with ' + str(skippedrange) + ' skipped of ' + str(setindex - istart) + ' and SortedResults has ' + str(len(threadSortedResults)) + '/' + str(maxresultsize) + ' at ' + '{0:.1f}'.format(combinationspersecond) + ' combinations/s', end='\r')
        if resumethreads:
            with open(logfilepath, 'wb') as logfile:
                pickle.dump(setindex, logfile, protocol=pickle.HIGHEST_PROTOCOL)
                pickle.dump(list(threadSortedResults.irange()), logfile, protocol=pickle.HIGHEST_PROTOCOL)
    if doprinting:
        print('')
    if resumethreads:
        with open(logfilepath, 'wb') as logfile:
            pickle.dump(setindex, logfile, protocol=pickle.HIGHEST_PROTOCOL)
            pickle.dump(list(threadSortedResults.irange()), logfile, protocol=pickle.HIGHEST_PROTOCOL)

    return [list(threadSortedResults.irange())]

#proecessthreadlen = 1 #len(processthread())



def printSortedList(filepath, sortedlist):
    global teamresistancesheaders
    nameidx = processedheaders.index('Name') 
    with open(filepath,'w', newline='') as csvoutfile:
        csvwriter = csv.writer(csvoutfile, delimiter=',')
        csvwriter.writerow(list(range(1,setsize + 1)) + teamstatsheaders + teamresistancesheaders)
        for row in sortedlist:
            betterrow = list(processedcsv[i+1][nameidx] for i in row[:setsize]) + row[setsize:]
            csvwriter.writerow(betterrow)



#*********** main ***********

def main():
    if not resumethreads:
        preprocesscsvdata(unprocessed_stats_path,processed_stats_path)
    else:
        loadprocessedcsvdata(processed_stats_path)
    
    if len(seededchoices_names) > 0:
        nameidx = processedheaders.index('Name') 
        for seedname in seededchoices_names:
            foundname = False
            for i in range(1,len(processedcsv)):
                rowname = processedcsv[i][nameidx]
                if rowname == seedname:
                    seededchoices.append(i-1)
                    foundname = True
                    break
            if not foundname:
                print('Couldnt find ' + seedname + ' in csv data')

    teamstatsScoreidx = teamstatsheaders.index('Score')
    sortedScoreidx = setsize + teamstatsScoreidx

    subsetpool = list(range(len(processedcsv) - 1 - len(seededchoices)))[::-1]
    totalcombinations = IndexedCombination( setsize - len(seededchoices), subsetpool).totalcombinations
    if len(seededchoices) > 0:
        print(str(int(totalcombinations)) + ' combinations using ' + str(len(processedcsv) - 1 ) + ' pkmn and ' + str(len(seededchoices)) + '/6 preselected')
    else:
        print(str(int(totalcombinations)) + ' combinations using ' + str(len(processedcsv) - 1 ) + ' pkmn')

    bestScores = SortedList(key=lambda x: -x[sortedScoreidx])

    nthreads = 1
    nthread = 0
    logfilepath = 'resumedata.' + str(nthread) + '.pickle'
    threaddata = [[]] * nthreads
    istart = int( nthread*totalcombinations/nthreads)
    iend = int( (nthread + 1)*totalcombinations/nthreads)
    setrange = [istart, iend, nthread == nthreads - 1, logfilepath]
    #print( 'thread ' + str(nthread+1) + ' processing ' + str(setrange))
    threadres = processthread(setrange)
    #print( 'thread ' + str(nthread+1) + ' finished')

    for someset in threadres[0]:
        bestScores.add(someset)
        if len(bestScores) > maxresultsize:
            bestScores.pop()

    printSortedList(os.path.join(currentdir,team_results_path), bestScores)
    print('done!         ')

if __name__ == '__main__':
    start = timeit.default_timer()
    main()
    stop = timeit.default_timer()
    print('finished in ' + str(round(stop - start,1)) + ' seconds')




