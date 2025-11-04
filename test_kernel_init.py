import asyncio
import logging
import sys

# Nastavíme debug logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sys.path.insert(0, '.')

print("1. Importujeme Kernel...")
from core.kernel import Kernel

print("2. Vytváříme Kernel instanci...")
kernel = Kernel()

print("3. Spouštíme kernel.initialize()...")

async def test_init():
    try:
        print("3a. Voláme await kernel.initialize()...")
        await asyncio.wait_for(kernel.initialize(), timeout=10.0)
        print("✅ Initialize dokončen!")
    except asyncio.TimeoutError:
        print("❌ TIMEOUT po 10 sekundách!")
    except Exception as e:
        print(f"❌ CHYBA: {e}")
        import traceback
        traceback.print_exc()

print("4. Spouštíme async test...")
asyncio.run(test_init())
print("5. HOTOVO!")
