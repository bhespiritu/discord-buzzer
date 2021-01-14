from aiohttp import web
import asyncio
import socketio
import discord
from threading import Thread

import os
from dotenv import load_dotenv
load_dotenv()
token = str(os.getenv("TOKEN"))

client = discord.Client()

sio = socketio.AsyncServer(cors_allowed_origins=['http://localhost:8080'])

app = web.Application()
sio.attach(app)

async def index(request):
    with open('index.html') as f:
        return web.Response(text=f.read(), content_type='text/html')
        
        
@sio.event
async def message(sid, data):
    print("message ", data)
    await sio.emit('message', data[::-1], room=sid)



@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    
class Player:
    def __init__(self, n, initScore=0):
        self.name = n
        self.score = initScore
    def __repr__(self):
        return self.name + " " + str(self.score)
        

players = {}
playerIDs = {}

useTeams = True
team1Name = "CringeLords"
team1Members = []
team1Score = 0

team2Name = "LordCringes"
team2Members = []
team2Score = 0

gui = None

dirty = True

def updateDisplay():
    global dirty
    dirty = True
    print("preparing to send")

async def sendUpdateDisplay():
    packet = ""
    if useTeams:
        packet += team1Name.lower()
        packet += "#"
        packet += str(team1Score)
        packet += '*'
        
        packet += team2Name.lower()
        packet += "#"
        packet += str(team2Score)
        packet += '*'
    else:
        for pID in players:
            player = players[pID]
            packet += player.name
            packet += '#'
            packet += str(player.score)
            packet += '*'
    print(packet)
    await sio.emit('state', packet)
    
@sio.event
async def connect(sid, environ):
    updateDisplay()
    print('connection established')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
        
    userID = message.author.id;
    
    if message.content.startswith("$join"):
        if len(message.content.split()) > 1:
            params = message.content.split(None,2)
            name = params[1].lower().replace('#','').replace('*','')
            newPlayer = Player(name)
            if userID in players.keys():
                await message.channel.send("You are already in here! use $leave to leave the game")
            else:
                players[userID] = newPlayer
                playerIDs[newPlayer.name] = userID 
                team1Members.append(newPlayer.name)
                gui.updateGUI()
                print(players)
                updateDisplay()
        else:
            await message.channel.send("Please specify a name! i.e $join Gregory")
        
    if message.content.startswith("$leave"):
        if userID in players.keys():
            name = players[userID].name
            if name in team1Members: team1Members.remove(name)
            if name in team2Members: team2Members.remove(name)
            del playerIDs[name]
            del players[userID]
            gui.updateGUI()
            
        
    if message.content.lower().startswith("$buzz"):
        name = ""
        if useTeams:
            pName = players[userID].name
            if pName in team1Members: name = team1Name
            if pName in team2Members: name = team2Name
        else:
            name = players[userID].name
        
        name = name.lower()
        print("buzz", name)
        
        await sio.emit('buzz', name)
            
        


## We bind our aiohttp endpoint to our app
## router
app.router.add_get('/', index)
app.router.add_static('/static', 'static/', name="style")

import tkinter as tk
import threading

async def run_tk(app, interval=0.05):
    global dirty
    try:
        while True:
            app.update()
            if dirty:
                dirty = False
                print("sending update")
                await sendUpdateDisplay()
            await asyncio.sleep(interval)
    except tkinter.TclError as e:
        if "application has been destroyed" not in e.args[0]:
            raise

class App():
    def on_close(self):
        pass

    def __init__(self):
        global team2Name
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.on_close)
        self.root.configure(bg='red')
        
        self.list_var1 = tk.StringVar()
        self.list_var2 = tk.StringVar()
        
        self.team1ScoreVar = tk.IntVar()
        self.team2ScoreVar = tk.IntVar()

        # main frame
        self.main_frame = tk.Frame(self.root)
        
        self.team1Frame = tk.Frame(self.main_frame)
        self.team2Frame = tk.Frame(self.main_frame)
        
        self.team1Name = tk.Entry(self.team1Frame)
        self.team1NameSet = tk.Button(self.team1Frame, text="Update", command=lambda: self.setTeam1Name())
        self.team2Name = tk.Entry(self.team2Frame)
        self.team2NameSet = tk.Button(self.team2Frame, text="Update", command=lambda: self.setTeam2Name())
        
        self.team1ScoreFrame = tk.Frame(self.team1Frame)
        self.team2ScoreFrame = tk.Frame(self.team2Frame)
        
        self.team1ScoreEntry = tk.Entry(self.team1ScoreFrame, textvariable=self.team1ScoreVar)
        self.team1ScoreSub5 = tk.Button(self.team1ScoreFrame, text="-5", command=lambda: self.setTeam1Score(-5))
        self.team1ScorePlus10 = tk.Button(self.team1ScoreFrame, text="+10", command=lambda: self.setTeam1Score(10))
        self.team1ScorePlus15 = tk.Button(self.team1ScoreFrame, text="+15", command=lambda: self.setTeam1Score(15))
        
        self.team1ScoreUpdate = tk.Button(self.team1Frame, text="Update Score", command=lambda: self.setTeam1Score(0))
        
        self.team2ScoreEntry = tk.Entry(self.team2ScoreFrame, textvariable=self.team2ScoreVar)
        self.team2ScoreSub5 = tk.Button(self.team2ScoreFrame, text="-5", command=lambda: self.setTeam2Score(-5))
        self.team2ScorePlus10 = tk.Button(self.team2ScoreFrame, text="+10", command=lambda: self.setTeam2Score(10))
        self.team2ScorePlus15 = tk.Button(self.team2ScoreFrame, text="+15", command=lambda: self.setTeam2Score(15))
        
        self.team2ScoreUpdate = tk.Button(self.team2Frame, text="Update Score", command=lambda: self.setTeam2Score(0))
        
        self.listbox1 = tk.Listbox(self.team1Frame, listvariable=self.list_var1, selectmode='multiple')
        self.listbox2 = tk.Listbox(self.team2Frame, listvariable=self.list_var2, selectmode='multiple')
        
        self.button_frame = tk.Frame(self.main_frame)

        self.all_to_right_button = tk.Button(self.button_frame, text='>>', command=self.move_to_right)
        self.one_to_right_button = tk.Button(self.button_frame, text='>', command=lambda: self.move_to_right(True))
        self.one_to_left_button = tk.Button(self.button_frame, text='<', command=lambda: self.move_to_left(True))
        self.all_to_left_button = tk.Button(self.button_frame, text='<<', command=self.move_to_left)

        # packing
        self.all_to_right_button.pack()
        self.one_to_right_button.pack()
        self.one_to_left_button.pack()
        self.all_to_left_button.pack()
        
        self.team1Frame.pack(side="left", anchor="w")
        self.team1Name.pack(side="top", anchor="n")
        self.team1NameSet.pack(side="top", anchor="n")
        self.listbox1.pack(side="top", anchor="n")
        self.team1ScoreFrame.pack(side="top", anchor="n")
        self.team1ScoreSub5.pack(side="left", anchor="w")
        self.team1ScoreEntry.pack(side="left", anchor="w")
        self.team1ScorePlus10.pack(side="left", anchor="w")
        self.team1ScorePlus15.pack(side="left", anchor="w")
        self.team1ScoreUpdate.pack(side="top", anchor="n")
        
        self.button_frame.pack(side='left')
        
        self.team2Frame.pack(side='right', anchor="e")
        self.team2Name.pack(side="top", anchor="n")
        self.team2NameSet.pack(side="top", anchor="n")
        self.listbox2.pack(side='top', anchor="n")
        self.team2ScoreFrame.pack(side="top", anchor="n")
        self.team2ScoreSub5.pack(side="left", anchor="w")
        self.team2ScoreEntry.pack(side="left", anchor="w")
        self.team2ScorePlus10.pack(side="left", anchor="w")
        self.team2ScorePlus15.pack(side="left", anchor="w")
        self.team2ScoreUpdate.pack(side="top", anchor="n")
        
        self.main_frame.pack()
        
        
    def setTeam1Name(self):
        global team1Name
        team1Name=self.team1Name.get()
        updateDisplay()
    def setTeam1Score(self, offset = 0):
        global team1Score
        val = self.team1ScoreVar.get() + offset
        team1Score=val
        self.team1ScoreVar.set(val)
        updateDisplay()
    def setTeam2Name(self):
        global team2Name
        team2Name=self.team2Name.get()
        updateDisplay()
    def setTeam2Score(self, offset = 0):
        global team2Score
        val = self.team2ScoreVar.get() + offset
        team1Score=val
        self.team2ScoreVar.set(val)
        updateDisplay()
    def move_to_right(self, only_one_item=False):
        global team2Members
        global team1Members
        if self.listbox1.curselection() == ():
            return

        # get tuple of selected indices
        if only_one_item:
            selection = (self.listbox1.curselection()[0],)
        else:
            selection = self.listbox1.curselection()

        # left all/selected values
        left_value_list = [line.strip(' \'') for line in self.list_var1.get()[1:-1].split(',')]
        left_selected_list = [left_value_list[index] for index in selection]
        for index in selection:
            del left_value_list[index]

        # values from right side
        right_value_list = [line.strip(' \'') for line in self.list_var2.get()[1:-1].split(',')]

        # merge w/o duplicates
        result_list = sorted(list(set(right_value_list + left_selected_list)))

        team2Members = result_list.copy()
        team1Members = left_value_list.copy()
        self.list_var1.set(value=team1Members)
        self.list_var2.set(value=team2Members)
        self.updateGUI()

    def move_to_left(self, only_one_item=False):
        global team2Members
        global team1Members
        if self.listbox2.curselection() == ():
            return
        # get tuple of selected indices
        if only_one_item:
            selection = (self.listbox2.curselection()[0],)
        else:
            selection = self.listbox2.curselection()

        # right all/selected values
        right_value_list = [line.strip(' \'') for line in self.list_var2.get()[1:-1].split(',')]
        right_selected_list = [right_value_list[index] for index in selection]
        for index in selection:
            del right_value_list[index]

        # values from left side
        left_value_list = [line.strip(' \'') for line in self.list_var1.get()[1:-1].split(',')]

        # merge w/o duplicates
        result_list = sorted(list(set(left_value_list + right_selected_list)))
        team1Members = result_list
        team2Members = right_value_list
        self.updateGUI()
        
    def updateGUI(self):
        global team2Members
        global team1Members
        self.list_var1.set(value=team1Members)
        self.list_var2.set(value=team2Members)

## We kick off our server
if __name__ == '__main__':
    gui = App()
    loop = asyncio.get_event_loop()
    loop.create_task(run_tk(gui.root))
    loop.create_task(client.start(token))
    loop.create_task(web.run_app(app))
    bot_thread = Thread(target=loop.run_forever())
    gui.root.quit()
    #web.run_app(app)
    
    
    