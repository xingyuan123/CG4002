import csv

from colorama import Fore

from Delegates.MyDelegate import MyDelegate
from Settings.Config import READING_COUNT, CSV, ACC_THRESHOLD, GYRO_THRESHOLD, WAITING_COUNT
from Settings.Constants import WINDOW_SIZE, GLOVE_READING_INDICES
from Utils import get_signed_int


class GloveDelegate(MyDelegate):
    def __init__(self, characteristic, device_id, color, data_in, data_out):
        MyDelegate.__init__(self, characteristic, device_id, color, data_in, data_out)
        self.is_logging = False
        self.logging_count = 0
        self.onset_buffer = []
        self.action_data = []
        self.action_id = 1

    def handle_data(self, packet_data):  # Override
        sensor_reading = tuple(get_signed_int(packet_data[i], packet_data[i + 1]) for i in GLOVE_READING_INDICES)
        self.onset_buffer.append(sensor_reading)
        self.update_onset_buffer(sensor_reading)

    def reset(self):  # Override
        super().reset()
        self.is_logging = False
        self.logging_count = 0
        self.onset_buffer = []
        self.action_data = []

    def update_onset_buffer(self, sensor_reading):
        if len(self.onset_buffer) > WINDOW_SIZE:
            self.onset_buffer.pop(0)
        if len(self.onset_buffer) == WINDOW_SIZE:
            if self.is_logging:
                if self.logging_count < READING_COUNT:
                    self.log_reading(sensor_reading)
                elif self.logging_count == READING_COUNT:
                    self.save_logs()
                elif self.logging_count == READING_COUNT + WAITING_COUNT:
                    self.stop_logging()
                self.logging_count += 1
            elif self.onset_detected():
                self.start_logging()

    def onset_detected(self):
        # Acceleration Readings
        old_acc_avg = sum([sum(reading[:3]) for reading in self.onset_buffer[:5]]) / 5
        new_acc_avg = sum([sum(reading[:3]) for reading in self.onset_buffer[5:]]) / 5
        acc_difference = int(abs(new_acc_avg - old_acc_avg))

        # Gyro Readings
        old_gyro_avg = sum([sum(reading[3:]) for reading in self.onset_buffer[:5]]) / 5
        new_gyro_avg = sum([sum(reading[3:]) for reading in self.onset_buffer[5:]]) / 5
        gyro_difference = int(abs(new_gyro_avg - old_gyro_avg))

        return acc_difference > ACC_THRESHOLD and gyro_difference > GYRO_THRESHOLD

    def log_reading(self, reading):
        self.action_data.append(reading)

    def start_logging(self):
        self.is_logging = True
        for reading in self.action_data[5:]:
            self.log_reading(reading)
        self.logging_count += 5
        print(self.color + f'<Device {self.device_id}> Started logging.' + Fore.RESET)

    def stop_logging(self):
        self.is_logging = False
        self.logging_count = 0
        self.onset_buffer = []
        self.action_data = []
        print(self.color + f'<Device {self.device_id}> Stopped logging, awaiting next action~' + Fore.RESET)

    def save_logs(self):
        self.data_out.put(str([self.device_id, self.action_data]))
        if CSV:
            self.write_to_csv()

    def write_to_csv(self):
        filename = f'device_{self.device_id}_glove_data_action_{self.action_id}.csv'
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['accX', 'accY', 'accZ', 'gyroX', 'gyroY', 'gyroZ'])
            for row in self.action_data:
                writer.writerow(row)
            self.action_id += 1
            print(self.color + f'<Device {self.device_id}> Saved action data to {filename}' + Fore.RESET)
