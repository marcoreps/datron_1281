import time
from datetime import datetime
import pyvisa as visa
import csv
import numpy


umin = -10.25
umax = 10.25
ustep = 0.25
wait_settle = 15
samples_per_meter_per_step = 1
NPLC = 100


timestr = datetime.utcnow().strftime("%Y%m%d-%H%M%S_")
instruments = dict()
rm = visa.ResourceManager()


instruments["3458A"]=rm.open_resource("GPIB0::22::INSTR")
instruments["3458A"].timeout = 200000
instruments["3458A"].clear()
instruments["3458A"].write("RESET")
instruments["3458A"].write("END ALWAYS")
instruments["3458A"].write("OFORMAT ASCII")
instruments["3458A"].write("BEEP")
print("ID? -> "+instruments["3458A"].query("ID?"))
instruments["3458A"].write("DCV 10")
instruments["3458A"].write("NDIG 9")
instruments["3458A"].write("NPLC 10")
instruments["3458A"].write("TARM AUTO")
instruments["3458A"].close()


instruments["3458B"]=rm.open_resource("GPIB0::23::INSTR")
instruments["3458B"].timeout = 200000
instruments["3458B"].clear()
instruments["3458B"].write("RESET")
instruments["3458B"].write("END ALWAYS")
instruments["3458B"].write("OFORMAT ASCII")
instruments["3458B"].write("BEEP")
print("ID? -> "+instruments["3458B"].query("ID?"))
instruments["3458B"].write("DCV 10")
instruments["3458B"].write("NDIG 9")
instruments["3458B"].write("NPLC 10")
instruments["3458B"].write("TARM AUTO")
instruments["3458B"].close()


instruments["J1281"]=rm.open_resource("GPIB0::16::INSTR")
instruments["J1281"].timeout = 200000
instruments["J1281"].write('*RST')
instruments["J1281"].write('*CLS')
time.sleep(3)
print(instruments["J1281"].query('*IDN?'))
instruments["J1281"].write("DCV 10,FILT_OFF,RESL8,FAST_ON")
instruments["J1281"].write("TRG_SRCE INT")
instruments["J1281"].close()


instruments["F5700A"]=rm.open_resource("GPIB0::1::INSTR")
instruments["F5700A"].clear()
instruments["F5700A"].write("*RST")
time.sleep(3)
instruments["F5700A"].write("EXTGUARD OFF")
print("*IDN? -> "+instruments["F5700A"].query("*IDN?"))
instruments["F5700A"].write("OUT "+str(umin)+" V")
instruments["F5700A"].write("OPER")
instruments["F5700A"].write("RANGELCK ON")
instruments["F5700A"].close()


time.sleep(300)


def finish():
    print("Shutting down...")
    #Reset the DMM and MFC####
    instruments["F5700A"].write("STBY")
    quit()


with open('csv/'+timestr+'REPS5700A_3458A_3458B_J1281_INL.csv', mode='w') as csv_file:
    csv_file.write("# INL run")
    csv_file.write("# wait_settle = "+str(wait_settle))
    csv_file.write("# samples_per_meter_per_step = "+str(samples_per_meter_per_step))
    csv_file.write("# NPLC = "+str(NPLC))
    
    fieldnames = ['vref', '3458A_volt','3458B_volt', 'J1281_volt']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    for u in numpy.arange(umin, umax+0.01, ustep):
        instruments["F5700A"]=rm.open_resource("GPIB0::1::INSTR")
        instruments["F5700A"].write("OUT "+str(u))
        instruments["F5700A"].close()
        print('main setting source to '+str(u)+'V')
        instruments["3458A"]=rm.open_resource("GPIB0::22::INSTR")
        instruments["3458A"].timeout = 200000
        instruments["3458A"].write("NPLC 10")
        instruments["3458A"].write("TARM AUTO")
        instruments["3458A"].close()
        instruments["3458B"]=rm.open_resource("GPIB0::23::INSTR")
        instruments["3458B"].timeout = 200000
        instruments["3458B"].write("NPLC 10")
        instruments["3458B"].write("TARM AUTO")
        instruments["3458B"].close()
        instruments["J1281"]=rm.open_resource("GPIB0::16::INSTR")
        instruments["J1281"].timeout = 200000
        instruments["J1281"].write("DCV 10,FILT_OFF,RESL8,FAST_ON")
        instruments["J1281"].write("TRG_SRCE INT")
        instruments["J1281"].close()
        time.sleep(wait_settle)
        instruments["3458A"]=rm.open_resource("GPIB0::22::INSTR")
        instruments["3458A"].timeout = 200000
        instruments["3458A"].write("NPLC 100")
        instruments["3458A"].write("TARM HOLD")
        instruments["3458A"].close()
        instruments["3458B"]=rm.open_resource("GPIB0::23::INSTR")
        instruments["3458B"].timeout = 200000
        instruments["3458B"].write("NPLC 100")
        instruments["3458B"].write("TARM HOLD")
        instruments["3458B"].close()
        instruments["J1281"]=rm.open_resource("GPIB0::16::INSTR")
        instruments["J1281"].timeout = 200000
        instruments["J1281"].write("DCV 10,FILT_OFF,RESL8,FAST_OFF")
        instruments["J1281"].write("TRG_SRCE EXT")
        instruments["J1281"].close()
        
        calibrator_out = u
        HP3458A_out = 0.0
        HP3458B_out = 0.0
        J1281_out = 0.0
        
        for n in range (samples_per_meter_per_step):
            instruments["3458A"]=rm.open_resource("GPIB0::22::INSTR")
            instruments["3458A"].timeout = 200000
            instruments["3458A"].write("TARM SGL")
            HP3458A_out += float(instruments["3458A"].read()) / samples_per_meter_per_step
            instruments["3458A"].close()
            instruments["3458B"]=rm.open_resource("GPIB0::23::INSTR")
            instruments["3458B"].timeout = 200000
            instruments["3458B"].write("TARM SGL")
            HP3458B_out += float(instruments["3458B"].read()) / samples_per_meter_per_step
            instruments["3458B"].close()
            instruments["J1281"]=rm.open_resource("GPIB0::16::INSTR")
            instruments["J1281"].timeout = 200000
            instruments["J1281"].write("X?")
            J1281_out += float(instruments["J1281"].read()) / samples_per_meter_per_step
            instruments["J1281"].close()
        
        writer.writerow({'vref': calibrator_out, '3458A_volt': HP3458A_out, '3458B_volt': HP3458B_out, 'J1281_volt': J1281_out})