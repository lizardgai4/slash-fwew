#!/usr/bin/env python3

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(Path.cwd(), ".env"))
api_url = os.environ.get("API_URL")

freq_table_onset = {
    # Consonent clusters will be added in runtime
}

freq_table_nuclei = {}

freq_table_end = {}

cluster_onsets = {"f":{},"s":{},"ts":{}}
non_cluster_onsets = {}

superclusters = {}

romanization = {
    # Vowels
    "a": "a",
    "i": "i",
    "ɪ": "ì",
    "o": "o",
    "ɛ": "e",
    "u": "u",
    "æ": "ä",
    # Diphthongs
    "aw": "aw",
    "ɛj": "ey",
    "aj": "ay",
    "ɛw": "ew",
    # Psuedovowels
    "ṛ": "rr",
    "ḷ": "ll",
    # Consonents
    "t": "t",
    "p": "p",
    "ʔ": "'",
    "n": "n",
    "k": "k",
    "l": "l",
    "s": "s",
    "ɾ": "r",
    "j": "y",
    "t͡s": "ts",
    "t'": "tx",
    "m": "m",
    "v": "v",
    "w": "w",
    "h": "h",
    "ŋ": "ng",
    "z": "z",
    "k'": "kx",
    "p'": "px",
    "f": "f",
    "r": "r",
    # Reef dialect
    "b": "px",
    "d": "tx",
    "g": "kx",
    "ʃ": "sy",
    "tʃ": "tsy",
    "ʊ": "ù",
    # mistakes and rarities
    "ʒ": "tsy",
    "": "",
    " ": ""
}

def table_manager_non_cluster_onsets(x:str):
    if not x in non_cluster_onsets:
        non_cluster_onsets[x] = 1
    else:
        non_cluster_onsets[x] += 1

def table_manager_cluster_onsets(x:str, y:str):
    if not y in cluster_onsets[x]:
        cluster_onsets[x][y] = 1
    else:
        cluster_onsets[x][y] += 1

def table_manager_nuclei(x:str):
    if x in freq_table_nuclei:
        freq_table_nuclei[x] += 1
    else:
        freq_table_nuclei[x] = 1

def table_manager_end(x:str):
    if x in freq_table_end:
        freq_table_end[x] += 1
    else:
        freq_table_end[x] = 1

def table_manager_supercluster(x:str, y:str):
    # Decode the cluster
    a = ""
    b = ""
    i = 1
    if y.startswith("ts") :
        a = "ts"
        i = 2
    elif y[0] in {"f","s"} :
        a = y[0]
    else:
        print("Some weird consonent cluster beginning")

    b = y[i:]
    
    if x in superclusters:
        if a in superclusters[x]:
            if b in superclusters[x][a]:
                i += 1
            else:
                superclusters[x][a].append(b)
        else:
            superclusters[x][a] = [b]
    else:
        superclusters[x] = {}
        superclusters[x][a] = [b]

def distros():
    global freq_table_onset
    global freq_table_nuclei
    global freq_table_end
    global cluster_onsets
    global non_cluster_onsets
    global superclusters

    z = 0

    dictionary = requests.get(f"{api_url}/list")
    dictionary = json.loads(dictionary.text)
    
    #print(a[5]['IPA'])

    #with open('dictionary-v2.txt', 'r') as a:
    for entry in dictionary:
        coda = ""
        start_cluster = ""

        words = entry['IPA'].split(' ')
        
        for word in words:
            syllables = word.split('.')

            for syllable in syllables:
                # get rid of the garbage
                syllable = syllable.replace("·", "").replace("ˈ","").removeprefix("[").removesuffix("]").removeprefix('ˌ')

                # keep track of where we are in the syllable
                i = 0
                        
                #
                # Syllable part 1
                #
                start_cluster = ""
                filled = False
                
                # Affricative?
                if(syllable.startswith('t͡s')):
                    if(syllable[3] in {"p", "k", "t"}):
                        if(syllable[4] == "'"):
                            i = 5
                        else:
                            i = 4
                        start_cluster = romanization[syllable[0:3]] + romanization[syllable[3:i]]
                        table_manager_cluster_onsets(romanization[syllable[0:3]], romanization[syllable[3:i]])
                        filled = True
                    elif(syllable[3] in {"l", "ɾ", "m", "n", "ŋ", "w", "j"}):
                        i = 4
                        start_cluster = romanization[syllable[0:3]] + romanization[syllable[3:i]]
                        table_manager_cluster_onsets(romanization[syllable[0:3]], romanization[syllable[3:i]])
                        filled = True
                    else:
                        i = 3
                # Some other clustarable thing?
                elif(syllable[0] in {"f", "s"}):
                    if(syllable[1] in {"p", "k", "t"}):
                        if(syllable[2] == "'"):
                            i = 3
                        else:
                            i = 2
                        start_cluster = romanization[syllable[0]] + romanization[syllable[1:i]]
                        table_manager_cluster_onsets(romanization[syllable[0]], romanization[syllable[1:i]])
                        filled = True
                    elif(syllable[1] in {"l", "ɾ", "m", "n", "ŋ", "w", "j"}):
                        i = 2
                        start_cluster = romanization[syllable[0]] + romanization[syllable[1:i]]
                        table_manager_cluster_onsets(romanization[syllable[0]], romanization[syllable[1:i]])
                        filled = True
                    else:
                        i = 1
                # Something that can ejective?
                elif(syllable[0] in {"p", "k", "t"}):
                    if(syllable[1] in {"'", "ʃ"}):
                        i = 2
                    else:
                        i = 1
                # None of the above
                elif(syllable[0] in {"ʔ", "l", "ɾ", "h", "m", "n", "ŋ", "v", "w", "j", "z", "b", "d", "g"}):
                    i = 1
                elif syllable[0] in {"ʃ", "ʒ"}:
                    i = 1
                    table_manager_cluster_onsets(romanization[syllable[0]][0:-1], romanization[syllable[0:i]][-1])
                    filled = True
                    
                if(not filled):
                   table_manager_non_cluster_onsets(romanization[syllable[0:i]])

                if coda != "" and start_cluster != "":
                    table_manager_supercluster(coda, start_cluster)
                    coda = ""
                    start_cluster = ""

                #
                # Nucleus of the syllable
                #
                if(i + 1 < len(syllable) and syllable[i+1] in {'j', 'w'}):
                    table_manager_nuclei(romanization[syllable[i:i+2]])
                    i += 2
                elif(i + 1 < len(syllable) and syllable[i] in {'r', 'l'}):
                    table_manager_nuclei(romanization[syllable[i:i+2]])
                    continue # Do not count psuedovowels towards the final consonent distribution
                else:
                    table_manager_nuclei(romanization[syllable[i]])
                    i += 1

                #
                # Syllable-final consonents
                #
                if(i >= len(syllable)):
                    table_manager_end(" ")
                    coda = ""
                elif(i + 1 == len(syllable)):
                    if(not syllable[i] in {":", '̣', "'"}): # fìtsenge lu kxanì
                        table_manager_end(romanization[syllable[i]])
                        coda = romanization[syllable[i]]
                    else:
                        table_manager_end(" ")
                elif(i + 1 < len(syllable)):
                    if(syllable.endswith('k̚')):
                        table_manager_end(romanization['k'])
                        coda = romanization['k']
                    elif(syllable.endswith('p̚')):
                        table_manager_end(romanization['p'])
                        coda = romanization['p']
                    elif(syllable.endswith('t̚')):
                        table_manager_end(romanization['t'])
                        coda = romanization['t']
                    elif(syllable.endswith('ʔ̚')):
                        table_manager_end(romanization['ʔ'])
                        coda = romanization['ʔ']
                    elif (syllable[i:i+2] == "ss"):
                        table_manager_end(" ") # oìsss only
                    else:
                        table_manager_end(romanization[syllable[i:i+2]])
                        coda = romanization[syllable[i:i+2]]
                else:
                    print("You should not be seeing this")
    
    #
    # Format the output
    #

    #freq_table_onset = dict(sorted(freq_table_onset.items(), key=lambda item: item[1], reverse = True))
    #cluster_onsets = dict(sorted(cluster_onsets.items(), key=lambda item: item[1], reverse = True))
    non_cluster_onsets = dict(sorted(non_cluster_onsets.items(), key=lambda item: item[1], reverse = True))
    freq_table_nuclei = dict(sorted(freq_table_nuclei.items(), key=lambda item: item[1], reverse = True))
    freq_table_end = dict(sorted(freq_table_end.items(), key=lambda item: item[1], reverse = True))
    
    return [non_cluster_onsets, cluster_onsets, freq_table_nuclei, freq_table_end, superclusters]
