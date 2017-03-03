from time import sleep

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

while True:
    m_data = get_data()
    clients_count = round(m_data["count"]/2)    # clients count = cross count / 2
    temperature = m_data["temp"]
    print("Clients count: {0}, Temperature: {1}".format(clients_count, temperature))

    sleep(TIMER_INTERVAL_SEC)



