#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyvisa as visa
import time
import logging


def finish():
    logging.info("Shutting down...")
    #Reset the DMM and MFC####
    F5700EP.write("OUT 0 V, 0 Hz")
    F5700EP.write("STBY")
    F5700EP.write("*RST")
    F5700EP.write("*CLS")
    F5700EP.close()
    dmm.write("*RST")
    dmm.close()
    quit()
    
    
settling_time = 60


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
logging.info("Starting ...")

rm = visa.ResourceManager()
F5700EP = rm.open_resource("TCPIP::192.168.0.88::GPIB0,1") # Ethernet GPIB Dongle
dmm = rm.open_resource("TCPIP::192.168.0.88::GPIB0,16") # Ethernet GPIB Dongle

#F5700EP = rm.open_resource('GPIB0::1::INSTR') # Local GPIB Dongle
##dmm = rm.open_resource('GPIB0::9::INSTR') # Local GPIB Dongle

########## DMM and MFC ##########   
F5700EP.write("*RST")
F5700EP.write("*CLS")
F5700EP.write("RANGELCK OFF")
#F5700EP.write("OUT 10 V, 0 Hz")
#F5700EP.write("RANGELCK ON")
F5700EP.write("STBY") 
F5700EP.write("OUT 0.0 V, 0 Hz")
F5700EP.write("EXTGUARD OFF")
time.sleep(5)
F5700EP.write("OPER")
time.sleep(5)
logging.info("SRC configured")

dmm.timeout = None
dmm.write("*RST")
time.sleep(2)
dmm.write("ENBCAL EXTNL")
logging.info("1281 configured")

########## DCV ADJUST ##########
### SHORT Input ###
for v in ['0.1','1','10','100','1000']:
    dmm.write("DCV "+v+",FILT_ON,RESL8,FAST_OFF,TWO_WR")
    logging.info("Cal DCV Zero "+v)
    time.sleep(settling_time)
    if(dmm.query("CAL?") != '0\n'):
        logging.info("Error")
        finish()
    
### FULL RANGE Input ###
for v in [0.1,1,10,100,1000]:
    for pol in [-1,1]:
        dmm.write("DCV "+str(v)+",FILT_ON,RESL8,FAST_OFF,TWO_WR")
        F5700EP.write("OUT "+str(pol*v))
        F5700EP.write("OPER")
        logging.info("Cal DCV Full Range "+str(v*pol))
        time.sleep(settling_time)
        if(dmm.query("CAL?") != '0\n'):
            logging.info("Error")
            finish()

F5700EP.write("OUT 0.0 V, 0 Hz")
time.sleep(10)

########## ACV ADJUST ##########
### 0.1V Range ###
dmm.write("ACV 0.1,RESL6,TWO_WR,FAST_OFF")
F5700EP.write("OUT 0.01 V, 1000 Hz")
logging.info("Cal ACV 1kHz 10 mV")
time.sleep(settling_time)
if(dmm.query("CAL?") != '0\n'):
    logging.info("Error")
    finish()
F5700EP.write("OUT 0.1 V, 1000 Hz")
logging.info("Cal ACV 1kHz 100 mV")
time.sleep(settling_time)
if(dmm.query("CAL?") != '0\n'):
    logging.info("Error")
    finish()
        
### Other Ranges ###
for v in [1,10,100,1000]:
    for scale in [0.001,1]:
        dmm.write("ACV "+str(v)+",RESL6,TWO_WR,FAST_OFF")
        F5700EP.write("OUT "+str(scale*v)+" V, 1000 Hz")
        F5700EP.write("OPER")
        logging.info("Cal ACV 1kHz "+str(v*scale)+" V")
        time.sleep(settling_time)
        if(dmm.query("CAL?") != '0\n'):
            logging.info("Error")
            finish()

F5700EP.write("OUT 0.0 V, 0 Hz")
time.sleep(10)


########## OHMS ADJUST ##########
### SHORT Input ###
F5700EP.write("OUT 0 OHM")
F5700EP.write("EXTSENSE ON")
F5700EP.write("OPER")
time.sleep(settling_time)
for r in [100,1000,10000,100000,1000000,10000000,100000000,1000000000]:
    dmm.write("OHMS "+str(r)+",FILT_ON,RESL8,FWR,FAST_OFF")
    logging.info("Cal OHMS Zero "+str(r)+" Ohm")
    if(dmm.query("CAL?") != '0\n'):
        logging.info("Error")
        finish()

### Nominal Input ###
for r in [100,1000,10000,100000,1000000,10000000]:
    F5700EP.write("OUT "+str(r)) 
    F5700EP.write("OUT?")
    res = F5700EP.read()
    cutstr = res.split(",")
    actual_res = float(cutstr[0])
    dmm.write("OHMS "+str(r)+",FILT_ON,RESL8,FWR,FAST_OFF")
    logging.info("Cal OHMS "+str(actual_res)+" Ohm")
    time.sleep(settling_time)
    if(dmm.query("CAL? "+str(actual_res)) != '0\n'):
        logging.info("Error")
        finish()

### HI_OHMS ###
F5700EP.write("EXTSENSE OFF")
F5700EP.write("OUT 100000000") 
F5700EP.write("OUT?")
res = F5700EP.read()
cutstr = res.split(",")
actual_res = float(cutstr[0])
dmm.write("HI_OHMS "+str(r)+",FILT_ON,RESL6,TWR,FAST_OFF")
logging.info("Cal OHMS "+str(actual_res)+" Ohm")
time.sleep(settling_time)
if(dmm.query("CAL? "+str(actual_res)) != '0\n'):
    logging.info("Error")
    finish()

### TRUE_OHMS ###
F5700EP.write("OUT 0")
F5700EP.write("EXTSENSE ON")
dmm.write("TRUE_OHMS 10,FILT_ON,RESL8,FAST_OFF")
logging.info("Cal TRUE_OHMS 10 Ohm Range Zero")
time.sleep(settling_time)
if(dmm.query("CAL? "+str(actual_res)) != '0\n'):
    logging.info("Error")
    finish()
F5700EP.write("OUT 10")
logging.info("Cal TRUE_OHMS 10 Ohm Range Full Scale")
time.sleep(settling_time)
if(dmm.query("CAL? "+str(actual_res)) != '0\n'):
    logging.info("Error")
    finish()
    
F5700EP.write("STBY")
    
while 1:
    str_input = input("connect the cable for current adjustments, and then input: go\n")
    if (str_input == 'go'):
        break
    else:
        print("input again")