# PyAgent.py

import Action
import Orientation
import Search
from itertools import combinations
import copy
    
class Agent:
    def __init__(self):
        
        self.agentHasGold = False
        self.agentHasArrow = True
        self.searchEngine = Search.SearchEngine() # Will keep a track of pits and wumpus
        self.actionList = []
        self.current_location = [1,1]
        self.destination = [1,1]
        self.current_orientation = Orientation.RIGHT
        self.visited = [[1,1]]
        self.queries = {}
        self.goldLocation = []
        self.other = []
        self.lastAction = []
        self.locationFoundStench = []
        self.wumpusDead = False
        self.wumpusLocation = []
        self.known = []
        self.breeze = []
        self.searchEngine.AddSafeLocation(1,1)        
        self.lastPerceptBreeze = False
    
    def Initialize(self):

        self.actionList = []
        self.Frontier = []
        self.wumpusDead = False
        self.agentHasArrow = True
        
        ##### Climb out if it could not find a path to the gold last time and had climbed out
        if self.current_location == [1,1] and self.agentHasGold == False and self.lastAction == Action.CLIMB:
        	self.actionList.append(Action.CLIMB)

        # Reinitialize that agent has gold
        self.agentHasGold = False

        if self.current_location != [1,1]:
            #### When it died somewhere #####
            if self.lastPerceptBreeze:
                self.known.append(self.current_location[:]) # Update pit in current location
                currentlocation = self.current_location[:]
                self.searchEngine.RemoveSafeLocation(self.current_location[0],self.current_location[1])
            else:
            	# This means it was killed by wumpus
                self.wumpusLocation.append(self.current_location[:]) # Update pit in current location
                self.searchEngine.RemoveSafeLocation(self.current_location[0],self.current_location[1])
            self.visited.append(self.current_location[:])
            self.current_location = [1,1]
            self.current_orientation = Orientation.RIGHT

        if self.goldLocation:
            #### When it found gold #####
            self.current_orientation = Orientation.RIGHT
            self.actionList = self.searchEngine.FindPath(self.current_location, self.current_orientation, self.goldLocation, Orientation.RIGHT)

        elif self.wumpusLocation and self.wumpusLocation not in self.visited and self.wumpusLocation not in self.known:
            if str(self.wumpusLocation) in self.queries.keys():
                if self.queries[str(self.wumpusLocation)] < 0.5:
                    #### When wumpus is alive and the agent knows wumpus location #####
                    #### Let's go wumpus hunting. Woohoo! #####
                    #### This will open up more safer locations for the agent #####
                    self.actionList=[]
                    if [self.wumpusLocation[0]-1,self.wumpusLocation[1]] in self.visited:
                        #### Wumpus is on the right of the agent #####
                        if self.current_location != [self.wumpusLocation[0]-1,self.wumpusLocation[1]]:
                            self.actionList += self.searchEngine.FindPath(self.current_location, self.current_orientation, [self.wumpusLocation[0]-1,self.wumpusLocation[1]], Orientation.RIGHT)
                        self.actionList.append(Action.SHOOT)
                    elif [self.wumpusLocation[0],self.wumpusLocation[1]-1] in self.visited:
                        #### Wumpus is above the agent #####
                        if self.current_location != [self.wumpusLocation[0],self.wumpusLocation[1]-1]:
                            self.actionList += self.searchEngine.FindPath(self.current_location, self.current_orientation, [self.wumpusLocation[0],self.wumpusLocation[1]-1], Orientation.RIGHT)
                        self.actionList.append(Action.TURNLEFT)
                        self.actionList.append(Action.SHOOT)

        self.lastPerceptBreeze = False

    ##### Form the Frontier #####
    def getFrontier(self):
        
        self.Frontier = []

        locationsToCheck = self.visited+self.known

        ##### Used for calculating frontier locations #####
        #####
        # If it's inside the 4x4 grid and not visited and not yet added as a frontier, then it must be a frontier
        #####
        for safeLocation_ in locationsToCheck:
            if safeLocation_[0]-1>0 and [safeLocation_[0]-1,safeLocation_[1]] not in self.visited and [safeLocation_[0]-1,safeLocation_[1]] not in self.Frontier:
                self.Frontier.append([safeLocation_[0]-1,safeLocation_[1]])

            if safeLocation_[0]+1<5 and [safeLocation_[0]+1,safeLocation_[1]] not in self.visited and [safeLocation_[0]+1,safeLocation_[1]] not in self.Frontier:
                self.Frontier.append([safeLocation_[0]+1,safeLocation_[1]])

            if safeLocation_[1]-1>0 and [safeLocation_[0],safeLocation_[1]-1] not in self.visited and [safeLocation_[0],safeLocation_[1]-1] not in self.Frontier:
                self.Frontier.append([safeLocation_[0],safeLocation_[1]-1])  

            if safeLocation_[1]+1<5 and [safeLocation_[0],safeLocation_[1]+1] not in self.visited and [safeLocation_[0],safeLocation_[1]+1] not in self.Frontier:
                self.Frontier.append([safeLocation_[0],safeLocation_[1]+1])


    ##### Checks if breeze is consistent with the locations in the frontier #####
    def breezeConsistency(self, pits):
        
        ##### Pits: Proabable frontier pit #####
        pits.extend(self.known) ##### Add known facts to the frontier pit locations

        for breeze_ in self.breeze:
            
            sum = 0

            ##### Check if breeze exists next to this probable pit (frontier) ######
            if breeze_[0]-1>0 and [breeze_[0]-1,breeze_[1]] in pits:
                sum += 1

            if breeze_[0]+1<5 and [breeze_[0]+1,breeze_[1]] in pits:
                sum += 1

            if breeze_[1]-1>0 and [breeze_[0],breeze_[1]-1] in pits:
                sum += 1

            if breeze_[1]+1<5 and [breeze_[0],breeze_[1]+1] in pits:
                sum += 1

            #### Means there is no breeze around the probable frontier pit #####
            if sum == 0:
                return 0

        return 1


    def calculateProbabilties(self):
        
        #### Get which locations are in the frontier #####
        self.getFrontier()

        ##### Calculate 'Other' as we now know the safe locations and the frontier #####
        self.other = []
        for i in range(1,5):
            for j in range(1,5):
                if [i,j] not in (self.Frontier+self.visited):
                    self.other.extend([[i,j]])

        ##### Save the probab of pit for each query in a dictionary where the key is the query location #####
        self.queries = {}

        for query in self.Frontier:

            p_pit_true = 0.0
            p_pit_false = 0.0

            ##### Frontier - Query #####
            frontier_ = [loc_ for loc_ in self.Frontier if query!=loc_]

            ##### Make various combinations of the frontier with pit T or F #####
            Combinations = []
            
            for cLen in range(len(frontier_)+1):
                Combinations.append([c for c in combinations(frontier_,cLen)])
            
            #### For each possible combination #####
            for c in Combinations:
                for combination in c:

                    numberOfTrue = 0
                    for _ in combination:
                        numberOfTrue+=1
                    
                    numberOfFalse = len(frontier_) - numberOfTrue

                    p = (0.2**numberOfTrue) * (0.8**numberOfFalse)

                    combination = list(combination)

                    if self.breezeConsistency([pit_ for pit_ in self.Frontier if pit_ in combination]):
                        p_pit_false += p

                    combination.append(query)

                    if self.breezeConsistency([pit_ for pit_ in self.Frontier if pit_ in combination]):
                        p_pit_true += p
            
            p_pit_true = p_pit_true*0.2
            p_pit_false = p_pit_false*0.8

            ##### Add the probability of the queries from frontier in the dictionary #####
            self.queries[str(query)]=p_pit_true/(p_pit_true+p_pit_false)

        ##### Print probabilities every time they are calculated #####
        self.print_probabilities()

    ##### Print probability of pit in each location #####
    def print_probabilities(self):

        #### Uncomment if you want to print #####
        # print ("Visited----->",self.visited)
        # print ("frontier (includes query)-----> ", self.Frontier)
        # print ("breeze----->", self.breeze)
        # print ("others ----->", self.other)
        # print ("queries ----->", self.queries)

        for j in reversed(range(1,5)):
            print ("\n+------+------+------+------+")
            for i in range(1,5):
                print ("|"),
                if (str([i,j]) in self.queries.keys()):
                    print "%0.2f"%round(self.queries[str([i,j])],2),
                elif [i,j] in self.known:
                    print "1.00",
                elif [i,j] in self.other:
                    print "0.20", # 0.2
                else:
                    print "%0.2f"%0.00,
            print ("|"),
        print ("\n+------+------+------+------+")
        print ("\n")

    ##### Find a safe unvisited location #####
    def whereNext(self):

        ##### If stink then shoot arrow to kill Wumpus and make a safer environment to play in #####
        if self.locationFoundStench and self.agentHasArrow == True and self.wumpusLocation not in self.visited:
            # Find unsafe location around
            # My agent is facing RIGHT most of the time in the search
            if self.locationFoundStench[0]!=4:
                ##### Goto the location where it found stench but couldn't move forward #####
                if self.current_location != self.locationFoundStench:
                    ##### If the location is not the current location then move to that location to kill the wumpus and open up opportunities #####
                    self.actionList += self.searchEngine.FindPath(self.current_location, self.current_orientation, self.locationFoundStench, Orientation.RIGHT)
                if self.current_orientation == Orientation.UP:
                    self.actionList.append(Action.TURNRIGHT)
                self.actionList.append(Action.SHOOT)
                
            elif self.locationFoundStench[0]==4:
                #### The wumpus was above it #####
                ##### Goto the location where it found stench but couldn't move forward #####
                if self.current_location != self.locationFoundStench:
                    ##### If the location is not the current location then move to that location to kill the wumpus and open up opportunities #####
                    self.actionList += self.searchEngine.FindPath(self.current_location, self.current_orientation, self.locationFoundStench, Orientation.RIGHT)
                if self.current_orientation == Orientation.RIGHT:
                    self.actionList.append(Action.TURNLEFT)
                elif self.current_orientation == Orientation.LEFT:
                    self.actionList.append(Action.TURNRIGHT)
                self.actionList.append(Action.SHOOT)
                
        else:
            ##### Since there are no locations to visit which have prob. 0 of having a pit #####
            ##### Time to decide... which location from frontier should the agent go to #####
            if self.queries.keys():
                #### Go wherever the value is the lowest #####
                minKey = min(self.queries, key=self.queries.get)

                #### That min. value should be less than 0.5 #####
                while self.queries[minKey] < 0.5:

                    #### Pop keys from the dict so as not to repeat while #####
                    self.queries.pop(minKey, None)
                    key = minKey[1:-1].split(",") ##### The key is stored as string so convert it into location format that is list
                    destination = [int(key[0]),int(key[1])]

                    #### Add the destination as a safe location for the search to find a path to it #####
                    if destination!=self.wumpusLocation:
                        self.searchEngine.AddSafeLocation(destination[0],destination[1])
                    
                    #### Let's check of a path exists to that location or not #####
                    if self.searchEngine.FindPath(self.current_location, self.current_orientation, destination, Orientation.RIGHT):
                        self.destination = destination
                        return
                    else:
                        self.searchEngine.RemoveSafeLocation(destination[0],destination[1])

                        #### Pop keys from the dict so as not to repeat while #####
                        self.queries.pop(minKey, None)

                        #### Get a new min prob location which can be visited #####
                        if self.queries.keys():
                            minKey = min(self.queries, key=self.queries.get)
                        else:
                            break

            ##### Can't go anywhere so let's go back #####
            self.destination = [1,1]
            return


    ##### Add safe locations around #####
    def addSafeLocations(self):
        if self.current_location[0]-1>0:
            self.searchEngine.AddSafeLocation(self.current_location[0]-1,self.current_location[1])

        if self.current_location[0]+1<5:
            self.searchEngine.AddSafeLocation(self.current_location[0]+1,self.current_location[1])

        if self.current_location[1]-1>0:
            self.searchEngine.AddSafeLocation(self.current_location[0],self.current_location[1]-1)

        if self.current_location[1]+1<5:
            self.searchEngine.AddSafeLocation(self.current_location[0],self.current_location[1]+1)

    ##### Remove safe locations around #####
    def removeSafeLocations(self):
        if self.current_location[1]-1>0:
            if [self.current_location[0],self.current_location[1]-1] not in self.visited:
                self.searchEngine.RemoveSafeLocation(self.current_location[0],self.current_location[1]-1)

        if self.current_location[1]+1<5:
            if [self.current_location[0],self.current_location[1]+1] not in self.visited:
                self.searchEngine.RemoveSafeLocation(self.current_location[0],self.current_location[1]+1)

        if self.current_location[0]-1>0:
            if [self.current_location[0]-1,self.current_location[1]] not in self.visited:
                self.searchEngine.RemoveSafeLocation(self.current_location[0]-1,self.current_location[1])

        if self.current_location[0]+1<5:
            if [self.current_location[0]+1,self.current_location[1]] not in self.visited:
                self.searchEngine.RemoveSafeLocation(self.current_location[0]+1,self.current_location[1])

    ##### Driver function for adding safe locations #####
    def updateSafetyOfLocationsAround(self, percept):

        #### If there was (no stench and no breeze) or (wumpus dead so we don't care about stench now and just check the breeze) #####
        if (percept['Stench'] == False and percept['Breeze'] == False) or (self.wumpusDead and percept['Breeze'] == False):
            self.addSafeLocations()
        elif self.wumpusLocation and percept['Stench'] and percept['Breeze'] == False:
            #### else if we know the location of wumpus and there is a stench and no breeze #####
            self.addSafeLocations()

            if self.wumpusDead == False:
                #### so location around are safe except for the wumpus's location which the agent knows #####
                self.searchEngine.RemoveSafeLocation(self.wumpusLocation[0],self.wumpusLocation[1])

        else:
            self.removeSafeLocations()

        #### Finally if the current location had not been visited before then add it to the visited locations #####
        if self.current_location not in self.visited:                
            self.visited.append(self.current_location[:])

    ##### Input percept is a dictionary [perceptName: boolean] #####
    def Process (self, percept):

        ##### Flag for checking Prob. calculation at each step #####
        FlagCheckProb = False

        ##### If location is being visited for the first time #####
        if self.current_location not in self.visited:
            self.updateSafetyOfLocationsAround(percept)
            ##### If there is a breeze then make a note of that. It'll come in handy during Frontier calculation #####
            if percept['Breeze']:
                self.breeze.append(self.current_location[:])
                if not self.agentHasGold:
                    self.actionList = []
        elif self.current_location == [1,1] and percept['Breeze'] and [1,1] not in self.breeze:
            ##### As [1,1] is already visited and Breeze detection get's missed #####
            self.breeze.append([1,1])

        ##### To check whether it was killed by a Pit or the Wumpus #####
        if percept['Breeze'] == True:
            self.lastPerceptBreeze = True

        ##### If no gold yet #####
        if (not self.agentHasGold):
            if percept['Glitter']:
                ##### Make path to go back to location (1,1) #####
                self.updateSafetyOfLocationsAround(percept)
                self.goldLocation = self.current_location[:]
                self.actionList = []
                self.actionList.append(Action.GRAB)
                self.agentHasGold = True
                self.actionList += self.searchEngine.FindPath(self.current_location, self.current_orientation, [1,1], Orientation.LEFT)
                self.actionList.append(Action.CLIMB)

        if FlagCheckProb == False:
            ##### Mandatory calculation before taking a step #####
            self.calculateProbabilties()
            if str(self.destination) in self.queries.keys():
                if self.queries[str(self.destination)]>0.5:
                    self.actionList = []
            FlagCheckProb = True

        ##### Found nothing on action list (general check) #####
        if not self.actionList:

            self.whereNext()

            #### If it could not find a safe location to visit then head back and climb out #####
            if not self.actionList:
                self.actionList += self.searchEngine.FindPath(self.current_location, self.current_orientation, self.destination, Orientation.RIGHT)
                if self.destination == [1,1]:
                    self.actionList.append(Action.CLIMB)

        #### Let's pop some action #####
        action = self.actionList.pop(0)

        ##### This part is for when gold has already been grabbed #####
        # If action is goforward and gold has been previously grabbed in last trial 
        # Now if next location is wumpus location and arrow is there then shoot arrow and add goforward in starting of action list
        forward_location = self.current_location[:]
        if action == Action.GOFORWARD and self.wumpusDead==False and self.agentHasArrow:
            if self.current_orientation == Orientation.RIGHT:
                forward_location[0] += 1
            elif self.current_orientation == Orientation.LEFT:
                forward_location[0] -= 1
            elif self.current_orientation == Orientation.UP:
                forward_location[1] += 1
            elif self.current_orientation == Orientation.DOWN:
                forward_location[1] -= 1

            if forward_location == self.wumpusLocation:
                if Action.SHOOT in self.actionList:
                    self.actionList.remove(Action.SHOOT)
                self.actionList = list([Action.GOFORWARD]) + self.actionList
                action = Action.SHOOT

        self.update_location_orientation(action)

        ##### Keep a check of last action incase it dies #####
        self.lastAction = action

        ##### Change availibility of arrow to kill wumpus #####
        if action == Action.SHOOT:
            self.agentHasArrow = False

        #### Hope for the best #####
        return action
    
    ##### Keeps track of location and orientation #####
    def update_location_orientation(self, action):
        if action == Action.GOFORWARD:
            if self.current_orientation == Orientation.UP:
                self.current_location[1] += 1
            elif self.current_orientation == Orientation.DOWN:
                self.current_location[1] -= 1
            elif self.current_orientation == Orientation.RIGHT:
                self.current_location[0] += 1
            else:
                self.current_location[0] -= 1
            self.searchEngine.AddSafeLocation(self.current_location[0],self.current_location[1])

        elif action == Action.TURNLEFT:
            self.decide_orientation(1) # add 1 to orientation on taking left
        elif action == Action.TURNRIGHT:
            self.decide_orientation(-1) # add -1 to orientation on taking right

    def decide_orientation (self, add_direction):
        self.current_orientation += add_direction
        if self.current_orientation > 3: # taking left from down will become right
            self.current_orientation -= 4
        if self.current_orientation < 0: # taking right from right will become down
            self.current_orientation += 4

    def GameOver(self, score):
        pass

# Global agent
myAgent = 0

def PyAgent_Constructor ():
    global myAgent
    myAgent = Agent()

def PyAgent_Destructor ():
    global myAgent
    # nothing to do here

def PyAgent_Initialize ():
    global myAgent
    myAgent.Initialize()

def PyAgent_Process (stench,breeze,glitter,bump,scream):

    print ("\n#########################\n")

    global myAgent
    percept = {'Stench': bool(stench), 'Breeze': bool(breeze), 'Glitter': bool(glitter), 'Bump': bool(bump), 'Scream': bool(scream)}
    
    #### If the last action was shoot and it missed the wumpus then the wumpus is above (UP) the agent
    if myAgent.lastAction == Action.SHOOT and percept['Scream'] == False and myAgent.wumpusDead == False:
        myAgent.wumpusLocation = [myAgent.current_location[:][0], myAgent.current_location[:][1]+1]
    elif percept['Scream']:
        #### If the wumpus died then update flag that it's dead #####
        myAgent.wumpusDead = True

        #### Also update the Wumpus's location #####
        forward_location = myAgent.current_location[:]
        if myAgent.current_orientation == Orientation.RIGHT:
                forward_location[0] += 1
        elif myAgent.current_orientation == Orientation.LEFT:
            forward_location[0] -= 1
        elif myAgent.current_orientation == Orientation.UP:
            forward_location[1] += 1
        elif myAgent.current_orientation == Orientation.DOWN:
            forward_location[1] -= 1

        ##### Decide whether wumpus location is safe or not based on breeze else if breeze is there then check prob. of pit #####
        myAgent.wumpusLocation = forward_location
        if percept['Breeze']==False:
            myAgent.searchEngine.AddSafeLocation(myAgent.wumpusLocation[0],myAgent.wumpusLocation[1])
        elif str(myAgent.wumpusLocation) in myAgent.queries:
            if myAgent.queries[str(myAgent.wumpusLocation)]:
                myAgent.searchEngine.AddSafeLocation(myAgent.wumpusLocation[0],myAgent.wumpusLocation[1])            

    ##### Location where wumpus might be #####
    ##### Will be used to kill wumpus and create safer places to move around #####
    if percept['Stench']:
        myAgent.locationFoundStench = myAgent.current_location[:]

    ##### Uncomment to stop at each iteration #####
    # raw_input("Press the <ENTER> key to continue...")
    return myAgent.Process(percept)

def PyAgent_GameOver (score):
    global myAgent
    myAgent.GameOver(score)
