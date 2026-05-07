import sys
import subprocess
from pathlib import Path


def run_pipeline(source_file, style="executive", depth="standard", yolo=True, extra_args=None):
    source_path = Path(source_file).resolve()
    if not source_path.exists():
        print(f"Error: file not found: {source_path}")
        return 1

    parts = [f"@full-analysis {source_path}", f"--style {style}", f"--depth {depth}"]
    if extra_args:
        parts.extend(extra_args)
    prompt = " ".join(parts)

    cmd = ["gemini", "--prompt", prompt]
    if yolo:
        cmd.append("--yolo")

    print(f"Invoking: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(Path(__file__).parent))
    return result.returncode


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else "/home/keithw/datasette/used_cars.csv"
    sys.exit(run_pipeline(source))
