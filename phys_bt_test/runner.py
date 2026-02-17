import argparse
import sys
import yaml
import time
from utils.builder import Builder
from utils.flasher import Flasher
from utils.monitor import Monitor

def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    parser = argparse.ArgumentParser(description='Physical Bluetooth Test Runner')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--test-dir', required=True, help='Path to the test application directory')
    parser.add_argument('--only-build', action='store_true', help='Only build the firmware, do not flash or run')
    args = parser.parse_args()

    print(f"Loading configuration from {args.config}...")
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config}' not found.")
        sys.exit(1)

    central_conf = config['devices']['central']
    peripheral_conf = config['devices']['peripheral']

    print("=== Phase 1: Building Firmware ===")
    
    # Build for Central
    print(f"Building for Central ({central_conf['board']})...")
    builder_central = Builder(args.test_dir, central_conf['board'], "build_central")
    if not builder_central.build(extra_args=["-DCONFIG_BT_CENTRAL=y"]):
        print("Build for Central failed!")
        sys.exit(1)

    # Build for Peripheral
    print(f"Building for Peripheral ({peripheral_conf['board']})...")
    builder_peripheral = Builder(args.test_dir, peripheral_conf['board'], "build_peripheral")
    if not builder_peripheral.build(extra_args=["-DCONFIG_BT_PERIPHERAL=y"]):
        print("Build for Peripheral failed!")
        sys.exit(1)

    if args.only_build:
        print("Build complete. Skipping flash and run.")
        sys.exit(0)

    print("=== Phase 2: Flashing Devices ===")

    # Flash Central
    print(f"Flashing Central (SN: {central_conf['serial_number']})...")
    flasher_central = Flasher("build_central", central_conf['serial_number'])
    if not flasher_central.flash():
         print("Flashing Central failed!")
         sys.exit(1)

    # Flash Peripheral
    print(f"Flashing Peripheral (SN: {peripheral_conf['serial_number']})...")
    flasher_peripheral = Flasher("build_peripheral", peripheral_conf['serial_number'])
    if not flasher_peripheral.flash():
        print("Flashing Peripheral failed!")
        sys.exit(1)

    print("=== Phase 3: Running Test ===")
    
    monitor_central = Monitor(central_conf['serial_port'], "CENTRAL")
    monitor_peripheral = Monitor(peripheral_conf['serial_port'], "PERIPHERAL")

    monitor_central.start()
    monitor_peripheral.start()

    # Wait for test completion (simplified logic for now)
    try:
        time.sleep(config.get('test', {}).get('timeout_sec', 30))
    except KeyboardInterrupt:
        print("Interrupted by user.")
    
    monitor_central.stop()
    monitor_peripheral.stop()

    print("Test finished.")

if __name__ == "__main__":
    main()
