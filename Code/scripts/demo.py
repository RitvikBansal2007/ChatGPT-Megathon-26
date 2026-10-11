"""Start the API and the web app together in live mode. Works on Windows, macOS and Linux.

    python scripts/demo.py            # from the Code/ directory
    make demo                         # same thing

What it does
- generates one-off secrets for this run (never written to disk)
- starts the API on 127.0.0.1:8000 and waits until /healthz answers
- starts the Streamlit app on http://127.0.0.1:8501 against that API
- stops both when you press Ctrl+C, or if either one dies

Clear failures instead of a blank page: it checks the generated packs exist, that
the ports are free, and that the API actually came up.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_api(url: str, proc: subprocess.Popen, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url + "/healthz", timeout=2) as r:
                if r.status == 200 and json.load(r).get("status") == "ok":
                    return True
        except OSError:
            pass
        time.sleep(0.5)
    return False


def stop(proc: subprocess.Popen | None) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--api-port", type=int, default=8000)
    ap.add_argument("--ui-port", type=int, default=8501)
    ap.add_argument("--no-live", action="store_true",
                    help="start only the web app, on the bundled sample data (no API)")
    args = ap.parse_args()
    os.chdir(CODE_DIR)

    if not args.no_live and not (CODE_DIR / "out" / "packs").is_dir():
        print("The evidence packs have not been built yet.\n"
              "  Run:  make pipeline        (a few minutes, fixed seed)\n"
              "  Or:   python scripts/demo.py --no-live   (bundled sample data, no API)")
        return 1
    for name, port in (("API", args.api_port), ("web app", args.ui_port)):
        if (name == "web app" or not args.no_live) and port_in_use(port):
            print(f"Port {port} is already in use, so the {name} cannot start.\n"
                  f"  Stop the other process, or choose another port "
                  f"(--{'api' if name == 'API' else 'ui'}-port).")
            return 1

    env = dict(os.environ)
    api = None
    api_url = f"http://127.0.0.1:{args.api_port}"
    try:
        if args.no_live:
            env["DEMO_MODE"] = "fixtures"
        else:
            env.update(
                ENV="demo",
                JWT_SECRET=secrets.token_urlsafe(48),
                DATA_KEY=base64.b64encode(os.urandom(32)).decode(),
                DEMO_MODE="live",
                API_BASE_URL=api_url,
            )
            api = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1",
                 "--port", str(args.api_port)], env=env)
            print(f"Starting the API on {api_url} ...")
            if not wait_for_api(api_url, api, timeout=40):
                print("The API did not come up. Scroll up for its error message.\n"
                      "Common causes: missing packs (run `make pipeline`), a missing dependency "
                      "(`pip install -e .`).")
                return 1
            print("API is healthy.")

        ui = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", "app/Home.py", "--server.address", "127.0.0.1",
             "--server.port", str(args.ui_port), "--server.headless", "true",
             "--browser.gatherUsageStats", "false"], env=env)
        print(f"\nOpen  http://127.0.0.1:{args.ui_port}   (Ctrl+C stops everything)\n")
        while True:
            if ui.poll() is not None:
                print("The web app stopped.")
                return ui.returncode or 0
            if api is not None and api.poll() is not None:
                print("The API stopped unexpectedly; stopping the web app.")
                stop(ui)
                return 1
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping ...")
        return 0
    finally:
        try:
            stop(ui)  # type: ignore[name-defined]
        except NameError:
            pass
        stop(api)


if __name__ == "__main__":
    sys.exit(main())
