import lightgbm as lgb
import numpy as np
import requests
import json
import os

STEAM_API_KEY = '54995C637A2B73ECFAF969FF36FD6344'
cwd = os.getcwd()
API = 'https://api.steampowered.com/IDOTA2Match_570/GetMatchHistoryBySequenceNum/v1'
seq = '7194292047'

with open(cwd+'//heroes.json', 'r') as file:
    heroes = json.load(file)

#convert hero number to name
#Args: heroes JSON from dotaconstants, hero ID
#126 heroes
def get_name(heroes, hid):
    name = heroes[str(hid)]['name']
    i = name.find("hero_")
    i += 5
    end = len(name)
    return name[i:end]

class Match:
    #More members to be added
    def __init__(self):
        self.match_id = ''
        self.seq_id = ''
        self.winner = ''
        self.picks = {}
        self.bans = {}

    #Args: individual match item from JSON
    #Returns 2 lists, {picks, bans}
    #Double picks (bans) are hidden within hero picks
    #Randoms do not show up in picks and happen only in R1,R2,D1,D2
    def read_draft(self,match):
        r_i = 1
        d_i = 1
        b_i = 1

        drafted = []
        #List of heroes from draft
        for pick in match["picks_bans"]:
            drafted.append(pick['hero_id'])

        #List of heroes in the game
        picked = []
        players = match["players"]
        randoms = 0
        #Find the randomed heroes and record them
        for player in players:
            picked.append(player['hero_id'])
            #Found a random
            randoms += 1 
            if(player['hero_id'] not in drafted):
                if(player['team_number'] == 0):
                    key = 'R'+str(r_i)
                    r_i += 1
                else:
                    key = 'D'+str(d_i)
                    d_i += 1
                self.picks[key] = str(player['hero_id'])

        

        # heroes = {}
        # #Dict of heroes in the game
        # players = match["players"]
        # for player in players:
        #     # heroes.append(player['hero_id'])
        #     heroes[player['hero_id']] = player['team_number']

        

        # print(heroes)

        #There can be up to 4 randomed heroes
        #Find the heroes that were randomed, and put them in first phase
        # randoms = 0
        # draftlen = len(match["picks_bans"])
        # draftlen = min(draftlen, 10)
        # for x in range(6,draftlen+1):
        #     if(match["picks_bans"][x]['is_pick'] == False): randoms = 10-x

        #Find each random and add it to picks
        # for x in range(randoms):
        #     for hero,side in heroes.items():
        #         try:
        #             for pick in match["picks_bans"]:
        #                 if(pick['hero_id'] == hero):
        #                     raise StopIteration
        #             if(side == 0):
        #                 key = 'R'+str(r_i)
        #                 r_i += 1
        #             else:
        #                 key = 'D'+str(d_i)
        #                 d_i += 1
        #             self.picks[key] = str(hero) 
        #         except StopIteration:
        #             continue
                
        
        #Find the remaining picks and bans
        draft = match["picks_bans"]
        self.match_id = match['match_id']
        for pick in draft:
            if(pick["is_pick"] == False or pick['hero_id'] not in picked):
                key = 'B'+str(b_i)
                b_i += 1
                self.bans[key] = pick['hero_id']        
            else:
                if(pick['team'] == 0):
                    key = 'R'+str(r_i)
                    r_i += 1
                else:
                    key = 'D'+str(d_i)
                    d_i += 1
                self.picks[key] = str(pick['hero_id'])

    def print(self):
        print('Match ID =',self.match_id, 'Winner =',self.winner)
        print(self.picks)
        print(self.bans)

    #From a match, generate a 10 row features matrix, and 10 row label array
    def features(self):
        #The heroes after 115 do not follow in order
        #Create a mask to correctly map hid to index in feature array
        mask = {}
        H = len(heroes)
        i = 0
        for hero in heroes:
            mask[hero] = i
            i+=1
        #Create the features matrix
        X = np.empty((0,510),bool)
        #Initialize an empty line for radiant and dire
        line = np.zeros((1,510),bool)

        #Indices of radiant, dire heroes, candidate, bans, pick#, side picking
        i_rad = 0
        i_dire = H
        i_pick = 2*H
        i_bans = 3*H
        i_order = 4*H
        i_side = 4*H + 5
        #Fill the bans - static information
        for val in self.bans.values():
            bid = mask[str(val)]
            line[0,i_bans+bid] = 1

        #Implement without iteration using 2x memory
        #Go Phase by phase
        #Iterate through 3 phases, append a feature array for the 10 picks
        for phase in range(1,4):
            num = 2*phase - 1
            Rpick = 'R'+str(num)
            Dpick = 'D'+str(num)
            #Setup - Make copy arrays for radiant and dire
            rline = line.copy()
            dline = line.copy()
            #Pick 1
            r_id1 = mask[self.picks[Rpick]]
            d_id1 = mask[self.picks[Dpick]]
            rline[0,i_pick + r_id1] = 1
            dline[0,i_pick + d_id1] = 1
            #Pick num and side
            rline[0,i_order + num-1] = 1
            dline[0,i_order + num-1] = 1
            rline[0,i_side] = 0
            dline[0,i_side] = 1
            #Append pick 1
            X = np.vstack((X,rline))
            X = np.vstack((X,dline))


            if(phase==1 or phase==2):
                num = 2*phase
                Rpick = 'R'+str(2*phase)
                Dpick = 'D'+str(2*phase)
                #Move current hero to team, erase current hero
                rline[0,i_rad + r_id1] = 1
                dline[0,i_dire + d_id1] = 1
                rline[0,i_pick + r_id1] = 0
                dline[0,i_pick + d_id1] = 0
                #Pick 2
                r_id2 = mask[self.picks[Rpick]]
                d_id2 = mask[self.picks[Dpick]]
                rline[0,i_pick + r_id2] = 1
                dline[0,i_pick + d_id2] = 1
                #Pick num
                rline[0,i_order + num-2] = 0
                dline[0,i_order + num-2] = 0
                rline[0,i_order + num-1] = 1
                dline[0,i_order + num-1] = 1
                #Append pick 2
                X = np.vstack((X,rline))
                X = np.vstack((X,dline))
                line[0,i_rad + r_id1] = 1
                line[0,i_dire + d_id1] = 1
                line[0,i_rad + r_id2] = 1
                line[0,i_dire + d_id2] = 1

        #Label matrix
        win = 0 if self.winner == 'R' else 1
        Y = np.full((10,1),win,bool)
        return X,Y

#Args: json of matches from API
#Returns: list of Matches
def parse_matches(matches):
    Matches = []
    real_dota = (1,22)
    for entry in matches:
        # print(entry['match_seq_num'])
        #Exclude matches based on various parameters
        #Exclude all game modes besides AP,Ranked
        if(entry['game_mode'] not in real_dota): continue
        #At least 6 players have to pick (4 randoms allowed)
        if(len(entry['picks_bans']) < 7): continue
        #Flags seem to detect something wrong
        if(entry['flags'] != 1): continue
        match = Match()
        match.winner = 'R' if(entry['radiant_win']) else 'D'
        match.read_draft(entry)
        Matches.append(match)
    return Matches


#Args: Dota 2 Seq ID, readwrite
#readwrite=0 means read from json, readwrite=1 means call API and write it to file
#Pulls next x matches in sequence from Dota API
#Optionally saves the API result JSON to file
#Returns: List of Matches, last match in sequence to start next one
def fetch_matches(seq, readwrite):
    if(readwrite):
        #Request 100 but API only returns 98?
        option = {'key':STEAM_API_KEY,'start_at_match_seq_num':seq,'matches_requested':100}
        r = requests.get(API,params=option)
        if(r.status_code != 200): 
            print("API Returned code ",r.status_code)
            quit()
        rjson = r.json()

        with open(cwd+'\\matches\\'+seq+'.json','w') as file:
            json.dump(rjson, file)

    else:
        with open(cwd+'//matches//'+seq+'.json','r') as file:
            rjson = json.load(file)

    # with open('valveDump.json','w') as f:
    #     json.dump(r.json(),f)

    result = rjson['result']['matches']
    end = result[len(result)-1]['match_seq_num']
    matches = parse_matches(result)
    return matches, end

    


# print(len(heroes))

total = 1000

data = np.zeros((0,510),bool)
label = np.zeros((0,1),bool)

#Fetch 1000 matches from the API
#Form features matrix as we go along
while(total < 1000):
    #Fetch 100 matches, beginning with seq
    #Counting up in seq goes back in time
    #JSON file naturally goes back in time
    matches, next = fetch_matches(seq,1)
    #Start with the next match in sequence
    seq = next+1
    #keep a running total of matches parsed
    total += len(matches)
    #Generate feature matrix from each match
    for match in matches:
        match.print()
        X,Y = match.features()
        data = np.vstack((data,X))
        label = np.vstack((label,Y))

matches, next = fetch_matches(seq,0)
for match in matches:
    # match.print()
    X,Y = match.features()
    names = np.empty((1,510),str)
    for i in range(126):
        #fill names
        pass
    data = np.vstack((data,names))
    data = np.vstack((data,X))
    label = np.vstack((label,Y))

#Print data to csv
np.savetxt('data.csv',data,'%d',delimiter=",")
np.savetxt('label.csv',label,'%d',delimiter=",")


# train_data = lgb.Dataset(data,label)
# # num_round = 10
# params = {
#     'objective': 'binary',
#     'metric': 'binary_logloss',
#     'learning_rate': 0.05,
#     'num_leaves': 64,
# }
# bst = lgb.train(params,train_data)
# bst.save_model('model.txt')