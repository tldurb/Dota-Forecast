import lightgbm as lgb
import numpy as np
import requests
import json
import os
import opendota

STEAM_API_KEY = '54995C637A2B73ECFAF969FF36FD6344'
cwd = os.getcwd()
# API = 'https://api.opendota.com/api/'
API = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/v1'

#convert hero number to name
#Args: heroes json from dotaconstants, hero ID
def get_name(heroes, hid):
    name = heroes[str(hid)]['name']
    i = name.find("hero_")
    i += 5
    end = len(name)
    return name[i:end]

#Args: json of public matches from dotabuff
#Returns: list of matchIDs
def get_ids(matches):
    ids = []
    for match in matches:
        id = int(match["match_id"])
        ids.append(id)
    return ids

#Args: json of individual match data from opendota
#Returns 2 lists, {picks, bans}
def read_draft(match):
    picks = {}
    r_i = 0
    d_i = 0
    bans = {}
    b_i = 0

    draft = match["picks_bans"]
    for i in draft:
        if(i["is_pick"] == 0):
            key = 'B'+str(b_i)
            b_i += 1
            name = get_name(heroes, i['hero_id'])
            bans[key] = name
        else:
            if(i['team'] == 0):
                key = 'R'+str(r_i)
                r_i += 1
            else:
                key = 'D'+str(d_i)
                d_i += 1
            name = get_name(heroes, i['hero_id'])
            picks[key] = name
    
    return picks, bans

#Args: Dota 2 Match ID
#Makes API Call to Opendota
#Optionally writes match data to json
def fetch_match(id,write):
    r = requests.get(API+'matches/'+str(id))
    if(r.status_code != 200): 
        print("API Returned code ",r.status_code)
        quit()

    match = r.json()
    if(write):
        with open(cwd+'\\matches\\'+str(id)+'.json', 'w') as file:
            json.dump(match,file)    
    return match

    
with open(cwd+'\\heroes.json', 'r') as file:
    heroes = json.load(file)

# option = {'less_than_match_id':'8565889687','min_rank':'80'}
# r = requests.get(API+'publicMatches',params=option)
# if(r.status_code != 200): quit()

# with open('publicMatches'+'.json','w') as f:
#     json.dump(r.json(),f)

# with open(id+'.json','w') as f:
#     json.dump(r.json(),f)

# with open('publicMatches.json','r') as f:
#     matches = json.load(file)

id = '8565889612'
seq = '7194292032'

# with open(cwd+'\\matches\\'+id+'.json', 'r') as file:
#     data = json.load(file)

# picks, bans = read_draft(data)

# print(picks)
# print(bans)

# with open(cwd+'\\matches\\publicMatches.json', 'r') as file:
#     matches = json.load(file)
#     ids = get_ids(matches)
    # print(ids)

# print(ids[0])
# fetch_match(ids[0],1)

# for i in range(1,50):
#     fetch_match(ids[i],1)

# with open(cwd+'\\'+str(id)+'.json', 'w') as file:
#     json.dump(r.json(),file)

# client = opendota.OpenDota()

# match = client.get_match(id)
# picks,bans = read_draft(match)
# print(picks)
# print(bans)

# option = {'key':STEAM_API_KEY,'start_at_match_seq_num':seq,'matches_requested':10}
# r = requests.get(API,params=option)
# print(r.url)

# result = r.json()
# matches = result['result']['matches']
# for match in matches:
#     print(match['match_id'])

# with open('valveDump.json','w') as f:
#     json.dump(r.json(),f)

mask = {}
i = 0
for hero in heroes:
    mask[hero] = i
    i+=1

print(mask)