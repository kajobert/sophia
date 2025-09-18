import pytest
import subprocess
import time
import httpx
import os

# --- Test pro Web API s reálným serverem ---

@pytest.fixture(scope="module")
def live_server():
    """
    Fixture, která spustí reálný Uvicorn server v testovacím režimu
    jako samostatný proces. Tímto způsobem testujeme celou aplikaci,
    včetně síťové vrstvy.
    """
    # Nastavíme proměnnou prostředí pro testovací režim.
    # To zajistí, že se v `web/api.py` aplikují mocky.
    env = os.environ.copy()
    env["SOPHIA_ENV"] = "test"

    # Spustíme server pomocí našeho nového robustního skriptu.
    # Použijeme Popen pro spuštění na pozadí.
    process = subprocess.Popen(
        [".venv/bin/python3", "run_web_server.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Počkáme, až bude server připraven, místo čtení logů.
    # Budeme se opakovaně pokoušet připojit, dokud to nevyjde nebo nevyprší čas.
    timeout = 20  # Maximální doba čekání v sekundách
    start_time = time.time()
    server_ready = False

    with httpx.Client() as client:
        while time.time() - start_time < timeout:
            try:
                # Zkusíme se připojit k základnímu endpointu.
                # Očekáváme 404, ale to nevadí. Důležité je, že spojení prošlo.
                client.get("http://127.0.0.1:8000/")
                server_ready = True
                print("Server je připraven.")
                break
            except httpx.ConnectError:
                # Server ještě není připraven, zkusíme to znovu za chvíli.
                time.sleep(0.5)
            except Exception as e:
                pytest.fail(f"Došlo k neočekávané chybě při čekání na server: {e}")

    if not server_ready:
        stdout, stderr = process.communicate(timeout=5)
        pytest.fail(
            f"Server neodpověděl v časovém limitu {timeout}s. Exit code: {process.poll()}\n"
            f"--- STDOUT ---\n{stdout.decode('utf-8') if stdout else ''}\n"
            f"--- STDERR ---\n{stderr.decode('utf-8') if stderr else ''}"
        )

    # Zkontrolujeme, zda se proces nespustil s chybou
    if process.poll() is not None:
        # Přečteme a dekódujeme stdout a stderr pro ladění
        stdout, stderr = process.communicate()
        pytest.fail(
            f"Server se nepodařilo spustit. Exit code: {process.returncode}\n"
            f"--- STDOUT ---\n{stdout.decode('utf-8')}\n"
            f"--- STDERR ---\n{stderr.decode('utf-8')}"
        )

    # Předáme proces testu
    yield process

    # Po skončení testu proces ukončíme
    process.terminate()
    process.wait()

def test_chat_endpoint_success(live_server):
    """
    Integrační test pro /chat endpoint.
    Ověřuje, že server běží, přijímá požadavky a vrací
    očekávanou strukturu dat v testovacím (mockovaném) režimu.
    """
    test_prompt = "Vytvoř jednoduchou webovou stránku."

    try:
        with httpx.Client() as client:
            response = client.post(
                "http://127.0.0.1:8000/chat",
                json={"prompt": test_prompt},
                timeout=30  # Zvýšený timeout pro případ pomalejšího CI
            )

        # 1. Ověření úspěšného HTTP statusu
        assert response.status_code == 200

        # 2. Ověření struktury JSON odpovědi
        data = response.json()
        assert "status" in data
        assert data["status"] == "success"
        assert "message" in data
        assert "final_context" in data

        # 3. Ověření obsahu v 'final_context' (mockovaná data)
        final_context = data["final_context"]
        assert "plan" in final_context
        assert "A simple test plan for the user request" in final_context["plan"]
        assert "code" in final_context
        assert "def add(a, b):" in final_context["code"]
        assert "test_results" in final_context
        assert "Kód je funkční" in final_context["test_results"]

        print("\n--- API Test Passed ---")
        print(f"Response: {data}")
        print("-----------------------")

    except httpx.ConnectError as e:
        pytest.fail(f"Nepodařilo se připojit k serveru na adrese http://127.0.0.1:8000. Ujistěte se, že server běží. Chyba: {e}")
    except Exception as e:
        pytest.fail(f"Došlo k neočekávané chybě během testu API: {e}")
