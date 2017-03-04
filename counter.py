import sqlite3
from time import sleep
import datetime

DEBUG = True
DEBUG_count = 0
# DEBUG = False

if DEBUG:
    import random
else:
    import minimalmodbus

COUNTER_PORT = "COM3"
COUNTER_MODBUS_ADDR = 11
COUNTER_MODBUS_START_REG = 32
COUNTER_MODBUS_COUNT_REG = 3

TIMER_INTERVAL_SEC = 10


def db_load(visitors, temperature):
    con = sqlite3.connect("test.db")
    cur = con.cursor()
    cur.execute("INSERT INTO Counter (Visitors, Temperature) values('%d','%d')"%(visitors, temperature))
    con.commit()
    con.close()



def get_data():
    if DEBUG:
        # Emulate registers values
        regs = []
        global DEBUG_count
        DEBUG_count = DEBUG_count + random.randint(1, 20)
        regs.append(DEBUG_count)
        regs.append(1)
        regs.append(random.randint(20, 30))
    else:
        regs = instrument.read_registers(COUNTER_MODBUS_START_REG, COUNTER_MODBUS_COUNT_REG)
    data = {"count": regs[0], "temp": regs[2]}
    return data


# --- START MODBUS ---
if not DEBUG:
    instrument = minimalmodbus.Instrument(COUNTER_PORT, COUNTER_MODBUS_ADDR)
    # minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True


#--- DB create ---
con = sqlite3.connect("test.db")
with con:
    cur = con.cursor()
    cur.execute("CREATE TABLE Counter(Id INTEGER primary key,Time CURRENT_TIMESTAMP, Visitors int, Temperature int)")

first_var = -1
# Initialization first_var
while True:
    if not datetime.datetime.now().second:
        first_var = get_data()["count"]
        print(first_var)
        sleep(1)
        break

current_minute = datetime.datetime.now().minute


while True:

    new_current_minute = datetime.datetime.now().minute

    if new_current_minute > current_minute:
        current_minute = new_current_minute
        m_data = get_data()
        temp_v = m_data["count"]
        clients_count = round((temp_v - first_var) / 2)  # clients count = cross count / 2
        first_var = temp_v
        temperature = m_data["temp"]
        db_load(clients_count, temperature)


        print("Clients count: {0}, Temperature: {1}".format(clients_count, temperature))

    sleep(TIMER_INTERVAL_SEC)


