"""Run INSIDE the CI image with --network none; synthetic options only.

This reproduces Supervisor's root-owned 0600 file, verifies the prior read
failure, then launches the actual App entrypoint and checks the corrected
non-root service access without printing configuration values.
"""
import hashlib
import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys
import time
from urllib.request import urlopen

sys.path.insert(0, "/opt/cl-control-web")


def main():
    from app.layout import DEFAULT

    service = pwd.getpwnam("clcontrol")
    directory = Path("/data")
    directory.mkdir(exist_ok=True)
    directory.chmod(0o755)
    options = directory / "options.json"
    synthetic = {
        "ai_provider": "openai",
        "ai_openai_model": "gpt-4.1-mini",
        "ai_openai_api_key": "synthetic-test-value-not-a-real-key",
        "ai_cloud_opt_in": True,
    }
    original = json.dumps(synthetic).encode("utf-8")
    options.write_bytes(original)
    os.chown(options, 0, 0)
    options.chmod(0o600)
    digest = hashlib.sha256(original).digest()
    layout = directory / "dashboard-layout.json"
    layout_bytes = json.dumps(DEFAULT).encode("utf-8")
    layout.write_bytes(layout_bytes)
    os.chown(layout, service.pw_uid, service.pw_gid)
    layout.chmod(0o600)

    # Reproduce the original defect without exposing any option contents.
    before = subprocess.run([
        "gosu", "clcontrol", sys.executable, "-c",
        "from app.studio_llm import read_options; assert read_options() == {}",
    ], capture_output=True)
    assert before.returncode == 0, "Root-only file should not be readable before initialization"

    process = subprocess.Popen(
        [sys.executable, "app/startup.py"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        ready = False
        for _ in range(100):
            if process.poll() is not None:
                raise AssertionError("App startup terminated unexpectedly")
            try:
                with urlopen("http://127.0.0.1:8099/api/health", timeout=1) as response:
                    ready = response.status == 200
                if ready:
                    break
            except OSError:
                time.sleep(0.1)
        assert ready, "App did not become healthy"
        status_lines = Path(f"/proc/{process.pid}/status").read_text().splitlines()
        for label, expected in (("Uid:", service.pw_uid), ("Gid:", service.pw_gid)):
            line = next(line for line in status_lines if line.startswith(label))
            assert all(int(value) == expected for value in line.split()[1:])
        assert next(line for line in status_lines if line.startswith("CapEff:")).split()[1] == "0000000000000000"
        info = options.stat()
        assert info.st_uid == 0 and info.st_gid == service.pw_gid
        assert stat.S_IMODE(info.st_mode) == 0o640
        assert stat.S_IMODE(directory.stat().st_mode) == 0o700
        assert hashlib.sha256(options.read_bytes()).digest() == digest
        assert layout.read_bytes() == layout_bytes
        assert sorted(p.name for p in directory.iterdir()) == ["dashboard-layout.json", "options.json"]
        after = subprocess.run([
            "gosu", "clcontrol", sys.executable, "-c",
            "from app.studio_llm import read_options, provider_status; "
            "s=provider_status(read_options()); "
            "assert s['provider']=='openai' and s['llm_ready'] and s['cloud_enabled']",
        ], capture_output=True)
        assert after.returncode == 0, "Service must recognize configured provider after initialization"
        print("PASS: root-only options reproduced; non-root web service healthy; provider readable; original bytes preserved; no network calls")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    main()
