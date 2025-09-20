# Tento skript schválí všechny received snapshoty jako approved v adresáři tests/snapshots/
# Používejte pouze po ruční kontrole, že received obsahuje očekávaný výstup!

import os
import shutil

SNAPSHOT_DIR = "tests/snapshots"

for fname in os.listdir(SNAPSHOT_DIR):
    if fname.endswith(".received.txt"):
        received = os.path.join(SNAPSHOT_DIR, fname)
        approved = os.path.join(SNAPSHOT_DIR, fname.replace(".received.txt", ".approved.txt"))
        if os.path.exists(received):
            shutil.copyfile(received, approved)
            print(f"Schváleno: {approved}")
