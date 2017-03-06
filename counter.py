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
TIMER_DATA_DOWNLOAD = 1  # minute
TIMER_DATA_SEND = None # time

FORMAT_DATE_TIME = "%y-%m-%d %H:%M:%S"


# --- DB create ---
def db_create():
    with sqlite3.connect("test.db") as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS counter(time PRIMARY KEY, visitors INT, temperature INT)")
        cur.close()


def db_load(time, visitors, temperature):
    with sqlite3.connect("test.db") as con:
        cur = con.cursor()
        cur.execute("INSERT INTO Counter (time, visitors, temperature) values(?, ?, ?)", (time, visitors, temperature))
        cur.close()


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


# --- create DB ---
db_create()


first_var = -1
# Initialization first_var
while True:
    if not datetime.datetime.now().second:
        first_var = get_data()["count"]
        sleep(1)
        break

current_minute = datetime.datetime.now()

if DEBUG:
    print("Начальный счетчик установлен в: ", first_var)
    print("Зафиксируем текущее время: ", current_minute)

while True:

    new_current_minute = current_minute + datetime.timedelta(minutes=TIMER_DATA_DOWNLOAD)

    # if new_current_minute > current_minute or (new_current_minute == 0 and current_minute == 59):
    if new_current_minute.minute == datetime.datetime.now().minute:
        if DEBUG:
            print("current time(minutes): {}, next time(minutes): {}, first counter {}".format(current_minute.minute, new_current_minute.minute, first_var))

        current_minute = new_current_minute
        m_data = get_data()
        temp_v = m_data["count"]
        clients_count = round((temp_v - first_var) / 2)  # clients count = cross count / 2
        first_var = temp_v
        temperature = m_data["temp"]
        db_load(new_current_minute.strftime(FORMAT_DATE_TIME), clients_count, temperature)

        if DEBUG:
            print("Time of recent record in DB: ", new_current_minute.strftime(FORMAT_DATE_TIME))

    sleep(TIMER_INTERVAL_SEC)




