import asyncio
import shutil
from threading import Thread
from queue import Queue
from DataServer import DataServer
from GameEngine import GameEngine
# from VizMqttClient import VizMqttClient
# from ai.MLP_wrapper import MLP as AI
# from test_ai.test_wrapper import test_AI as AI
from dummy_AI import Dummy_AI as AI
from Helper import MsgHelper, Status

def print_line():
    w, _ = shutil.get_terminal_size()
    print('='*w)

async def main():
    password    = '1234567890123456'
    num_players = 2

    status      = Status(num_players, freeplay=True)
    msg_helper  = MsgHelper(password)

    # Game Engine
    engine = GameEngine(num_players)
    eng_in = Queue()
    eval_in = Queue()

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
    data_recv  = Thread(target=data_server.recv_data_p, args=(status, data_in, eng_in, viz_out,))
    data_recv.daemon = True
    
    # 2. AI generate action using data (dummy)
    ai_action  = Thread(target=ai.run_ai, args=(status, data_in, eng_in,))

    # 3. Perform action: Updates game state, send to hardware & viz, eval server
    eng_action = Thread(target=engine.perform_action, args=(status, eng_in, viz_out, data_out,)) 

    # # 4. MQTT: Send to Visualiser
    # viz_send   = Thread(target=viz_client.send_to_broker, args=(viz_out,))

    # 7. TCP: Send data back to data client
    data_send  = Thread(target=data_server.send_data, args=(data_out,))

    queues  = [eng_in, eval_in, data_in] # viz_out, data_out
    threads = [ai_action, eng_action, data_send] #, viz_send]

    # receive initial connect packets
    data_recv.start()
    status.connect[0].wait()

    # clear queues
    for queue in queues:
        with queue.mutex:
            queue.queue.clear()
    # start threads
    for thread in threads: 
        thread.daemon = True
        thread.start()
    
    print('Starting freeplay')
    print_line()
    while True:
        pass

if __name__ == "__main__":
    print('Initialising Ultra96')
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
