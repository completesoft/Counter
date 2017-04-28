import sqlite3
from time import sleep
import datetime
import requests
import os
from json import load




DEBUG = True
DEBUG_count = 0
# DEBUG = False

if DEBUG:
    import random
else:
    import minimalmodbus

CONFIG = load(open('config.json', 'r'))

DB_LITE = CONFIG["DB"]

COUNTER_PORT = CONFIG["COUNTER_PORT"]
COUNTER_MODBUS_ADDR = CONFIG["COUNTER_MODBUS_ADDR"]
COUNTER_MODBUS_START_REG = CONFIG["COUNTER_MODBUS_START_REG"]
COUNTER_MODBUS_COUNT_REG = CONFIG["COUNTER_MODBUS_COUNT_REG"]

# offset from the COUNTER_MODBUS_START_REG
MOD_BUS_REG_COUNTER = CONFIG["MOD_BUS_REG_COUNTER"]
MOD_BUS_REG_TEMPERATURE = CONFIG["MOD_BUS_REG_TEMPERATURE"]
MOD_BUS_REG_ENERGY = CONFIG["MOD_BUS_REG_ENERGY"]

TIMER_INTERVAL_SEC = CONFIG["TIMER_INTERVAL_SEC"]
TIMER_DATA_DOWNLOAD_MIN = CONFIG["TIMER_DATA_DOWNLOAD_MIN"]  # minute
TIMER_DATA_SEND = CONFIG["TIMER_DATA_SEND"] # time

FORMAT_DATE_TIME = CONFIG["FORMAT_DATE_TIME"]


def get_data_DB():
    with sqlite3.connect(DB_LITE) as con:
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
    if not os.access(DB_LITE, os.F_OK):
        with sqlite3.connect(DB_LITE) as con:
            cur = con.cursor()
            cur.execute("CREATE TABLE IF NOT EXISTS counter(time PRIMARY KEY, visitors INT, temperature INT, conditioner INT)")
            cur.execute("CREATE TABLE IF NOT EXISTS event_list (id_event INT UNIQUE, description TEXT)")
            for event in CONFIG["ALERT_EVENT"][0].items():
                cur.execute("INSERT INTO event_list (id_event, description) values(?, ?)", (event[1], event[0]))

            cur.execute("CREATE TABLE IF NOT EXISTS event(time PRIMARY KEY, id_event INT, FOREIGN KEY(id_event) REFERENCES event_list(id_event))")
            cur.close()


def db_write(time, visitors=0, temperature=0, conditioner=0, alert=False, discription_id=0):
    with sqlite3.connect("test.db") as con:
        cur = con.cursor()
        if not alert:
            cur.execute("INSERT INTO counter (time, visitors, temperature, conditioner) values(?, ?, ?, ?)", (time, visitors, temperature, conditioner))
        else:
            cur.execute("INSERT INTO event (time, id_event) values(?, ?)", (time, discription_id))
        cur.close()


def get_data():
    if DEBUG:
        # Emulate registers values
        regs = []
        global DEBUG_count
        DEBUG_count = DEBUG_count + random.randint(1, 20)
        regs.append(DEBUG_count)
        regs.append(1)
        regs.append(random.randint(0,1))
        # regs.append(0)
    else:
        regs = instrument.read_registers(COUNTER_MODBUS_START_REG, COUNTER_MODBUS_COUNT_REG)
    data = {"count": regs[MOD_BUS_REG_COUNTER], "temp": regs[MOD_BUS_REG_TEMPERATURE], "a_c_power": regs[MOD_BUS_REG_ENERGY]}
    return data


# --- START MODBUS ---
if not DEBUG:
    instrument = minimalmodbus.Instrument(COUNTER_PORT, COUNTER_MODBUS_ADDR)
    # minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True


# --- create DB ---
db_create()


# Initialization: first_var - visitors counter
a_c_power = 0
first_var = get_data()["count"]
current_minute = datetime.datetime.now()

if DEBUG:
    print("Начальный счетчик установлен в: ", first_var)
    print("Зафиксируем текущее время: ", current_minute)

while True:

    new_current_minute = current_minute + datetime.timedelta(minutes=TIMER_DATA_DOWNLOAD_MIN)
    a_c_power += TIMER_INTERVAL_SEC*(get_data()["a_c_power"])

    print("Текущие показания работы кондиционера: ",a_c_power)

    # Visitors counter and temperature recording
    if new_current_minute.minute == datetime.datetime.now().minute:
        if DEBUG:
            print("current time(minutes): {}, next time(minutes): {}, first counter {}".format(current_minute.minute, new_current_minute.minute, first_var))

        current_minute = new_current_minute
        m_data = get_data()

        # Console debug info
        print("За прошедшую минуту данные по регистрам для записи в бд:")
        for reg, val in m_data.items():
            if reg=="a_c_power": val=a_c_power
            print("Регистр: ", reg, " | данные: ", val)

        # Sensor failure
        if m_data["count"] < first_var:
            first_var = m_data["count"]
            db_write(new_current_minute.strftime(FORMAT_DATE_TIME), alert=True, discription_id=CONFIG["ALERT_EVENT"][0]["ALERT_VISITOR_SENSOR"])
            temperature = m_data["temp"]
            db_write(new_current_minute.strftime(FORMAT_DATE_TIME), temperature=temperature)

            if DEBUG:
                print("Sensor Failure")
            sleep(TIMER_INTERVAL_SEC)
            continue

        temp_v = m_data["count"]
        clients_count = round((temp_v - first_var) / 2)  # clients count = cross count / 2
        temperature = m_data["temp"]
        db_write(new_current_minute.strftime(FORMAT_DATE_TIME), clients_count, temperature, a_c_power)

        first_var = temp_v
        a_c_power = 0

        if DEBUG:
            print("Time of recent record in DB: ", new_current_minute.strftime(FORMAT_DATE_TIME))

    sleep(TIMER_INTERVAL_SEC)








