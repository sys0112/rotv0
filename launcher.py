import sys
import os
import threading
import webbrowser
import time
import socket


def _resource_path(relative: str) -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)


def _data_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


os.environ["ROTTO_TEMPLATE_PATH"] = _resource_path("templates")
os.environ["ROTTO_DB_PATH"] = os.path.join(_data_dir(), "lotto.db")
os.environ["ROTTO_LICENSE_PATH"] = os.path.join(_data_dir(), "license.key")

from app import app  # noqa: E402

PORT = 5000


def _run_server():
    app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    server = threading.Thread(target=_run_server, daemon=True)
    server.start()

    for _ in range(30):
        time.sleep(0.3)
        try:
            import urllib.request
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}", timeout=1)
            break
        except Exception:
            pass

    ip = _local_ip()
    print("=" * 42)
    print("  [로또 번호 분석기] 실행 중")
    print(f"  PC  :  http://localhost:{PORT}")
    print(f"  폰  :  http://{ip}:{PORT}  (같은 Wi-Fi)")
    print("  이 창을 닫으면 서버가 종료됩니다.")
    print("=" * 42)

    webbrowser.open(f"http://localhost:{PORT}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
