# How to set up Ext Comms

### On Relay Laptop
Note: Keep all terminals open throughout evaluation  

Set up MQTT broker
1. Run Docker Desktop.
2. On a terminal, run `docker run -p 8080:8080 -p 1883:1883 hivemq/hivemq4` to start the MQTT broker.
3. On another terminal, run `ssh -R 1883:localhost:1883 xilinx@makerslab-fpga-24.d2.comp.nus.edu.sg`. This sets up the reverse ssh tunelling from the Ultra96 to the MQTT broker. 

### On Visualiser
1. Input the ipv4 address for the relay laptop as the Broker Address, and press Connect

### On Eval Server Laptop
1. Download `eval_server.zip` from Canvas. 
2. cd into server, run command `bash run_server.sh`.
3. Open `index.html` in your browser and input relevant fields:
    - Eval Server IP Addr: 127.0.0.1
    - Group name: B06
    - Password: 1234567890123456
    - **Click "The Team does not have a visualizer"**
4. The page should now look like this. Take note of the port number. 

### On Ultra96 Laptop
1. ssh into Ultra96 using `ssh xilinx@makerslab-fpga-24.d2.comp.nus.edu.sg`. 
2. On another terminal, run `ssh -R 8888:localhost:<index.html port> xilinx@makerslab-fpga-24.d2.comp.nus.edu.sg`. This sets up the reverse ssh tunelling from the Ultra96 to the MQTT broker. 
2. cd into `ext_comms` and run `python Ultra96.py`. 
4. Terminal should print `[DATA] Waiting for client connection on port 53087`. Take note of the port number.

### On Relay Laptop
Set up the data client (to communicate with Ultra96)  
5. Run `DataClient.py`. 
6. Input port as seen on `Ultra96`. 
