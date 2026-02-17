import subprocess
import os

class Builder:
    def __init__(self, source_dir, board, build_dir):
        self.source_dir = source_dir
        self.board = board
        self.build_dir = build_dir

    def build(self, extra_args=None):
        cmd = [
            "west", "build",
            "-b", self.board,
            "-d", self.build_dir,
            self.source_dir,
            "--"
        ]
        if extra_args:
            cmd.extend(extra_args)
        
        print(f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode == 0
        except Exception as e:
            print(f"Build exception: {e}")
            return False
