import sqlite3
from time import sleep
import datetime
import requests

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


def get_data_DB():
    with sqlite3.connect("test.db") as con:
        cur = con.cursor()
        cur.execute("SELECT time, visitors, temperature FROM counter ")
        all_rec = cur.fetchall()
        cur.close()
    return all_rec


def send_data(url, all_rec):
    headers = {"content-type": "application/json"}
    url = url
    data = all_rec
    r = requests.post(url, headers=headers, json=data)
    return r


def db_clear(send_date_RESPONSE=False):
    OK = send_date_RESPONSE
    if OK:
        with sqlite3.connect("test.db") as con:
            cur = con.cursor()
            cur.execute("DELETE FROM counter")
            cur.close()
            print("All - Send, All - Clear")
    else:
        print("Data NOT Send")


# --- DB create ---
def db_create():
    with sqlite3.connect("test.db") as con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS counter(time PRIMARY KEY, visitors INT, temperature INT)")
        cur.execute("CREATE TABLE IF NOT EXISTS event(time PRIMARY KEY, description TEXT)")
        cur.close()


def db_load(time, visitors=0, temperature=0, alert=False, discription="Sensor Failure" ):
    with sqlite3.connect("test.db") as con:
        cur = con.cursor()
        if not alert:
            cur.execute("INSERT INTO counter (time, visitors, temperature) values(?, ?, ?)", (time, visitors, temperature))
        else:
            cur.execute("INSERT INTO event (time, description) values(?, ?)", (time, discription))
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


# Initialization first_var current time
first_var = get_data()["count"]
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

        # Sensor failure
        if m_data["count"] < first_var:
            first_var = m_data["count"]
            db_load(new_current_minute.strftime(FORMAT_DATE_TIME), alert=True)
            if DEBUG:
                print("Sensor Failure")
            sleep(TIMER_INTERVAL_SEC)
            continue

        temp_v = m_data["count"]
        clients_count = round((temp_v - first_var) / 2)  # clients count = cross count / 2
        first_var = temp_v
        temperature = m_data["temp"]
        db_load(new_current_minute.strftime(FORMAT_DATE_TIME), clients_count, temperature)

        if DEBUG:
            print("Time of recent record in DB: ", new_current_minute.strftime(FORMAT_DATE_TIME))

    sleep(TIMER_INTERVAL_SEC)







