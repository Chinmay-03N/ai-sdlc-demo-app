from __future__ import annotations

from collections.abc import Iterator
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://127.0.0.1:5000"


@pytest.fixture(scope="session", autouse=True)
def app_server() -> Iterator[None]:
    backend_dir = Path(__file__).resolve().parent.parent / "backend"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "invoice_app.api.main:app",
            "--app-dir",
            "src",
            "--port",
            "5000",
        ],
        cwd=backend_dir,
    )

    try:
        for _ in range(100):
            if process.poll() is not None:
                raise RuntimeError(f"Uvicorn exited during startup with code {process.returncode}.")
            try:
                with urlopen("http://127.0.0.1:5000", timeout=0.2):
                    break
            except URLError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Uvicorn did not become ready at http://127.0.0.1:5000.")

        yield
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
