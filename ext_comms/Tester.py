import asyncio
import shutil
from threading import Thread, Event
from queue import Queue
from DataServer import DataServer
from GameEngine import GameEngine
# from VizMqttClient import VizMqttClient
# from ai.MLP_wrapper import MLP as AI
from dummy_AI import Dummy_AI as AI
from Helper import MsgHelper, Player
from time import sleep

def print_line():
    w, _ = shutil.get_terminal_size()
    print('='*w)
    
async def main():
    password    = '1234567890123456'
    num_players = 2
    msg_helper  = MsgHelper(password)

    status = {
        1: Player(1),
        2: Player(2)
    }
    connect = [Event() for _ in range(7)]
    if num_players == 1:
        # unused devices
        for i in [1, 5, 6]:
            connect[i].set()

    round_end = Event()
    game_end  = Event()

    # Game Engine
    engine = GameEngine(num_players, does_not_have_visualizer=True)
    eng_in = Queue()
    eval_out = Queue()

    # AI
    ai = AI()

    # # Visualiser
    # viz_client = VizMqttClient()
    viz_out = Queue()

    # Data Server
    data_server = DataServer(msg_helper)
    data_in  = Queue()
    data_out = Queue()
    await data_server.accept()
    
    # 1. TCP: Receive data from data client
    data_recv  = Thread(target=data_server.recv_data_p, args=(status, connect, data_in, eng_in,))
    
    # 2. AI generate action using data (dummy)
    ai_action  = Thread(target=ai.run_ai, args=(status, data_in, eng_in, game_end,))

    # 3. Perform action: Updates game state, send to hardware & viz, eval server
    eng_action = Thread(target=engine.perform_action, args=(eng_in, status, eval_out, viz_out, data_out,)) 

    # # 4. MQTT: Send to Visualiser
    # viz_send = Thread(target=viz_client.send_to_broker, args=(viz_out,))

    # 7. TCP: Send data back to data client
    data_send  = Thread(target=data_server.send_data, args=(data_out,))

    threads = [data_recv, ai_action, eng_action, data_send] #, viz_send]

    print_line()
    for thread in threads: 
        thread.daemon = True
        thread.start()
    
    while True:
        for _ in range(num_players):
            data = eval_out.get()['game_state']
            data_out.put(data)
        round_end.set()
        sleep(2)
        for player in status.values():
            player.action_done.clear()
            player.is_shot.clear()
        
        # start next round
        print_line()
        round_end.clear()

if __name__ == "__main__":
    print('Initialising Ultra96')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
