import subprocess

class Flasher:
    def __init__(self, build_dir, serial_number):
        self.build_dir = build_dir
        self.serial_number = serial_number

    def flash(self):
        # NOTE: Depending on the runner (jlink, nrfjprog, pyocd), the argument might be --dev-id or --snr
        # For nRF devices often used with 'west flash', --dev-id usually works for JLink.
        cmd = [
            "west", "flash",
            "-d", self.build_dir,
            "--dev-id", self.serial_number
        ]
        
        print(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"Flash exception: {e}")
            return False
