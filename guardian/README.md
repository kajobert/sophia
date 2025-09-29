# Projekt Strážce (Guardian)

Tento projekt je jednoduchý monitorovací agent napsaný v Pythonu. Jeho účelem je aktivně sledovat klíčové systémové prostředky v sandboxovém prostředí, ve kterém operuje agent Jules.

## Cíle

- Monitorovat využití diskového prostoru.
- Sledovat dostupnou operační paměť.
- Aktivně hlídat počet otevřených souborových deskriptorů, aby se předešlo překročení systémového limitu (1024).
- Logovat veškerá zjištění do souboru `guardian.log`.

## Spuštění

Agent se spouští pomocí následujícího příkazu z kořenového adresáře projektu:

```bash
python3 guardian/agent.py
```

Agent je navržen tak, aby běžel nepřetržitě na pozadí.