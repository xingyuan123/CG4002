import multiprocessing
from multiprocessing import Queue

from Beetle import beetle_process
from Settings.Config import SERVER_PORT, ULTRA_96, SERVER_IP, SERVER
from Settings.Constants import DEVICE_ADDRESSES, DEVICE_IDS, DEVICE_COLORS, ULTRA_96_IP
from Server.DataClient import DataClient


def start_server_processes():
    if ULTRA_96:
        data_client = DataClient(ULTRA_96_IP, SERVER_PORT)
    else:
        data_client = DataClient(SERVER_IP, SERVER_PORT)
    print('<Server> Connected.')
    data_recv = multiprocessing.Process(target=data_client.recv_data, args=(queues,))
    data_recv.start()
    processes.append(data_recv)
    data_send = multiprocessing.Process(target=data_client.send_data, args=(data_out,))
    data_send.start()
    processes.append(data_send)


def start_beetle_processes():
    for device_name, address in DEVICE_ADDRESSES.items():
        if not address:
            continue
        device_process = multiprocessing.Process(target=beetle_process,
                                                 args=(
                                                     address,
                                                     DEVICE_IDS[device_name],
                                                     DEVICE_COLORS[device_name],
                                                     queues[DEVICE_IDS[device_name]],
                                                     data_out))
        device_process.start()
        processes.append(device_process)


# Main
if __name__ == '__main__':
    processes = []
    queues = [Queue() for i in range(7)]
    data_out = Queue()

    if SERVER:
        start_server_processes()
    start_beetle_processes()

    for p in processes:
        p.join()
