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
    
    


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    
    if message.content.startswith("$join"):
        name = message.content.replace("$join","").strip().lower();
        print("Added " + name)
        await sio.emit("join", name);
        
    if message.content.startswith("$leave"):
        name = message.content.replace("$leave","").strip().lower();
        print("Removed " + name)
        await sio.emit("leave", name);
    
    if message.content.startswith("$score"):
        name = message.content.replace("$score","").strip().lower();
        print("Incremented " + name)
        await sio.emit("increment", name);
        
    if message.content.startswith("$buzz"):
        name = message.content.replace("$buzz","").strip().lower();
        print("Buzz In " + name)
        await sio.emit("buzz", name);
    
    if message.content.startswith("$set"):
        name, count = message.content.replace("$set","").strip().lower().split(None, 1)
        print("Set " + name + " to " + count)
        await sio.emit("set", name + "#" + count);
        
    

## We bind our aiohttp endpoint to our app
## router
app.router.add_get('/', index)
app.router.add_static('/static', 'static/', name="style")

## We kick off our server
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(client.start(token))
    loop.create_task(web.run_app(app))
    bot_thread = Thread(target=loop.run_forever())

    #web.run_app(app)
    
    
    