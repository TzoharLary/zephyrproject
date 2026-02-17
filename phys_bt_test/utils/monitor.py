import threading
import serial
import time

class Monitor:
    def __init__(self, port, name, baudrate=115200):
        self.port = port
        self.name = name
        self.baudrate = baudrate
        self.stop_event = threading.Event()
        self.thread = None

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True # Daemonize thread
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=2)

    def _run(self):
        try:
            with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                print(f"[{self.name}] Connected to {self.port}")
                while not self.stop_event.is_set():
                    line = ser.readline()
                    if line:
                        try:
                            decoded_line = line.decode('utf-8').strip()
                            if decoded_line:
                                print(f"[{self.name}] {decoded_line}")
                        except UnicodeDecodeError:
                            print(f"[{self.name}] <Binary Data>")
        except serial.SerialException as e:
            print(f"[{self.name}] Serial Error: {e}")
        except Exception as e:
            print(f"[{self.name}] Error: {e}")
