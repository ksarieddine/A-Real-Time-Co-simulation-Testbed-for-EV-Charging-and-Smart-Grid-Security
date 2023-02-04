import sys
sys.path.append(r'C:/OPAL-RT/HYPERSIM/hypersim_R6.1.3.o698/Windows/HyApi/C/py')
import HyWorksApi
import ScopeViewApi
import time
import socket
import pickle
import os

ip = '000.000.000.000'#sys.argv[1]
port = 444 #int(sys.argv[2])
# Set up a TCP/IP server
tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
# Bind the socket to server address and port 81
server_address = (ip, port)
tcp_socket.bind(server_address)
 
# Listen on port 81
tcp_socket.listen(1)

def receiveData(d):
    for k, v in sorted(d.items()):
        time.sleep(v[0])
        for i in range(len(v[1])):
            for j in range(len(v[2])):
                for l in range(len(v[3])):
                    for m in range (len(v[4])):
                        if(v[1][i] == "setLoad"):
                            # print(k)
                            setLoad(v[2][j], v[3][l][0], str(v[4][m][0])) # P0
                            setLoad(v[2][j], v[3][l][1], str(v[4][m][1])) # Q0
                            # HyWorksApi.setComponentParameter('Ld6',

def setLoad(loadName, componentName, value):
    # print(loadName, " ", componentName, " ", value)
    HyWorksApi.setComponentParameter(loadName, componentName, value)
    volt = HyWorksApi.getComponentParameter(loadName, componentName)
    print('Load: ' + volt[0] + volt[1])

# receiveData(d)

def startHypersim():
    #Open the design
    try:
        HyWorksApi.startAndConnectHypersim()
        designPath = r'E:/Workspace EV/EV/MODEL/IEEE_9Bus_autobackup_2022_04_12_03_39_25.ecf'
        HyWorksApi.openDesign(designPath)
        
        HyWorksApi.setPreference('simulation.calculationStep', '50e-6')
        calcStep = HyWorksApi.getPreference('simulation.calculationStep')
        
        print('calcStep = ' + calcStep)
        print('code directory : ' + HyWorksApi.getPreference('simulation.codeDirectory'))
        print('mode : ' + HyWorksApi.getPreference('simulation.architecture'))
        
        HyWorksApi.mapTask()
        HyWorksApi.genCode()
        HyWorksApi.startLoadFlow()
        HyWorksApi.startSim()

        time.sleep(5) # time to load.
        print('Simulation Started')
        scopeViewProcess = ScopeViewApi.openScopeView()    
        ScopeViewApi.loadTemplate("E:\Workspace EV\EV\MODEL\Temp_9_bus.xml")
        ScopeViewApi.setTimeLength(100.0)
        ScopeViewApi.setTrig(True)
        ScopeViewApi.setSync(True)
        print('Scope View Loaded.')
    except e as err:
        if(connection):
            connection.close()
        ScopeViewApi.close()
        HyWorksApi.stopSim()
startHypersim()

try:
    # ScopeViewApi    

    while True:
        print("Waiting for connection")
        connection, client = tcp_socket.accept()

        print("Connected to client IP: {}".format(client))
            
        # Receive and print data 32 bytes at a time, as long as the client is sending something
        while True:
            # volt = HyWorksApi.getComponentParameter('Ld6', 'Po')
            # print('Load: ' + volt[0] + volt[1])

            data = connection.recv(2048)
            data = pickle.loads(data)
            print("Received data")

            if(data):
                ScopeViewApi.startAcquisition() 
                time.sleep(5)
                receiveData(data)
            break

# Stop the Simulation
    time.sleep(10)
except Exception as err:
    print(err)
finally:
    print("Simulation is stopped")
    if(connection):
        connection.close()
    ScopeViewApi.close()
    HyWorksApi.stopSim()
    # HyWorksApi.closeDesign(designPath)
    # HyWorksApi.closeHyperWorks()