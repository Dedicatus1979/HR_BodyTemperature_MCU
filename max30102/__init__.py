# This work is a lot based on:
# - https://github.com/sparkfun/SparkFun_MAX3010x_Sensor_Library
#   Written by Peter Jansen and Nathan Seidle (SparkFun)
#   This is a library written for the Maxim MAX30105 Optical Smoke Detector
#   It should also work with the MAX30105, which has a Green LED, too.
#   These sensors use I2C to communicate, as well as a single (optional)
#   interrupt line that is not currently supported in this driver.
#   Written by Peter Jansen and Nathan Seidle (SparkFun)
#   BSD license, all text above must be included in any redistribution.
#
# - https://github.com/kandizzy/esp32-micropython/blob/master/PPG/ppg/MAX30105.py
#   A port of the library to MicroPython by kandizzy
#
# This driver aims at giving almost full access to Maxim MAX30102 functionalities.
#                                                                          n-elia
# Make corrections and deletions with Dedicatus1979 at 2024-03-06


from ustruct import unpack
from utime import sleep_ms

from max30102.circular_buffer import CircularBuffer

MAX3010X_I2C_ADDRESS = 0x57

MAX30105_SAMPLE_AVG_MASK = ~0b11100000

MAX30105_PULSE_AMP_MEDIUM = 0x7F
MAX30105_PULSE_AMP_HIGH = 0xFF

MAX_30105_EXPECTED_PART_ID = 0x15


class SensorData:
    def __init__(self):
        self.red = CircularBuffer(4)

class MAX30102(object):
    def __init__(self,
                 i2c,
                 i2c_hex_address=MAX3010X_I2C_ADDRESS,
                 ):
        self.i2c_address = i2c_hex_address
        self._i2c = i2c
        self._active_leds = None
        self._pulse_width = None
        self._multi_led_read_mode = None
        self._sample_rate = None
        self._sample_avg = None
        self._acq_frequency = None
        self._acq_frequency_inv = None
        self.sense = SensorData()

    def setup_sensor(self, led_mode, sample_rate, led_power, sample_avg, pulse_width):
        self.soft_reset()
        self.set_fifo_average(sample_avg)
        self.set_bitmask(0x08, 0xEF, 0x10)
        self.set_led_mode(led_mode)
        self.set_bitmask(0x0A, 0x9F, 0x60)
        self.set_sample_rate(sample_rate)
        self.set_pulse_width(pulse_width)
        self.i2c_set_register(0x0C, led_power)
        self.i2c_set_register(0x10, led_power)
        self.clear_fifo()

    def __del__(self):
        self.shutdown()

    def soft_reset(self):
        self.set_bitmask(0x09, 0xBF, 0x40)
        curr_status = -1
        while not ((curr_status & 0x40) == 0):
            sleep_ms(10)
            curr_status = ord(self.i2c_read_register(0x09))

    def shutdown(self):
        self.set_bitmask(0x09, 0x7F, 0x80)

    def set_led_mode(self, LED_mode):
        self.set_bitmask(0x09, 0xF8, 0x02)
        self.bitmask(0x11, 0xF8, 0x01)
        self._active_leds = LED_mode
        self._multi_led_read_mode = LED_mode * 3

    def set_sample_rate(self, sample_rate):
        self.set_bitmask(0x0A, 0xE3, 0x0C)
        self._sample_rate = sample_rate
        self.update_acquisition_frequency()

    def set_pulse_width(self, pulse_width):
        self.set_bitmask(0x0A, 0xFC, 0x03)
        self._pulse_width = 0x03

    def set_fifo_average(self, number_of_samples):
        self.set_bitmask(0x08, MAX30105_SAMPLE_AVG_MASK, 0x60)
        self._sample_avg = number_of_samples
        self.update_acquisition_frequency()

    def update_acquisition_frequency(self):
        if None in [self._sample_rate, self._sample_avg]:
            return
        else:
            self._acq_frequency = self._sample_rate / self._sample_avg
            from math import ceil

            self._acq_frequency_inv = int(ceil(1000 / self._acq_frequency))

    def clear_fifo(self):
        self.i2c_set_register(0x04, 0)
        self.i2c_set_register(0x05, 0)
        self.i2c_set_register(0x06, 0)

    def i2c_read_register(self, REGISTER, n_bytes=1):
        self._i2c.writeto(self.i2c_address, bytearray([REGISTER]))
        return self._i2c.readfrom(self.i2c_address, n_bytes)

    def i2c_set_register(self, REGISTER, VALUE):
        self._i2c.writeto(self.i2c_address, bytearray([REGISTER, VALUE]))
        return

    def set_bitmask(self, REGISTER, MASK, NEW_VALUES):
        newCONTENTS = (ord(self.i2c_read_register(REGISTER)) & MASK) | NEW_VALUES
        self.i2c_set_register(REGISTER, newCONTENTS)
        return

    def bitmask(self, reg, slotMask, thing):
        originalContents = ord(self.i2c_read_register(reg)) & slotMask
        self.i2c_set_register(reg, originalContents | thing)

    def fifo_bytes_to_int(self, fifo_bytes):
        value = unpack(">i", b'\x00' + fifo_bytes)
        return (value[0] & 0x3FFFF) >> self._pulse_width

    def available(self):
        number_of_samples = len(self.sense.red)
        return number_of_samples

    def pop_red_from_storage(self):
        return self.sense.red.pop()

    def check(self):
        read_pointer = ord(self.i2c_read_register(0x06))
        write_pointer = ord(self.i2c_read_register(0x04))
        if read_pointer != write_pointer:
            number_of_samples = write_pointer - read_pointer
            if number_of_samples < 0:
                number_of_samples += 32
            for i in range(number_of_samples):
                fifo_bytes = self.i2c_read_register(0x07, self._multi_led_read_mode)
                if self._active_leds > 0:
                    self.sense.red.append(self.fifo_bytes_to_int(fifo_bytes[0:3]))
                return True
        else:
            return False
