# Tento soubor slouží pouze k otestování chybějícího .env v izolovaném procesu.
# Importuje pouze konfiguraci Sophia, což by mělo selhat pokud .env chybí.

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    # Nejprve importujeme výjimku z jejího nového modulu
    from core.exceptions import MissingEnvFileError
    # Poté se pokusíme importovat konfigurační modul, což by mělo selhat
    import core.config
except MissingEnvFileError:
    # Odchytíme specifickou chybu a vypíšeme očekávanou zprávu
    print(".env soubor nebyl nalezen")
    # Ukončíme s kódem 0, protože jsme chybu očekávali a správně ošetřili
    sys.exit(0)
except Exception as ex:
    # Jakákoliv jiná chyba je stále neočekávaná
    print(f"Neočekávaná výjimka: {ex}")
    sys.exit(1)
