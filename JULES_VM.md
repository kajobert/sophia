# Protokol Nomád: Analýza Sandbox Prostředí (JULES_VM)

Tento dokument obsahuje detailní informace o virtuálním prostředí (sandboxu), ve kterém operuje agent Jules. Cílem je identifikovat potenciální omezení a zajistit stabilní a efektivní vývoj v rámci projektu Sophia/Nomád.

## 1. Souhrn Systému

- **Distribuce OS:** Ubuntu 24.04.2 LTS (Noble Numbat)
- **Architektura:** x86_64
- **Jádro Linuxu:** 6.8.0
- **Hostname:** devbox
- **Hypervisor:** KVM

## 2. Hardwarové Specifikace

### 2.1. Procesor (CPU)

- **Model:** Intel(R) Xeon(R) Processor @ 2.30GHz
- **Počet jader:** 4
- **Architektura:** x86_64
- **Virtualizace:** Plná (full)

### 2.2. Operační Paměť (RAM)

- **Celková velikost:** 7.8 GiB
- **Swap:** 0 B (Není alokován)

### 2.3. Diskové Úložiště

- **Celková velikost:** 20 GB
- **Připojeno jako:** `/` (overlayfs)

## 3. Nainstalovaný Software a Nástroje

### 3.1. Systémové nástroje

- **GCC:** 13.3.0

### 3.2. Vývojové prostředí

- **Python:** 3.12.11
- **uv:** 0.8.3
- **Node.js:** v22.17.1

## 4. Síťová Konfigurace

- **Lokální rozhraní (lo):** `127.0.0.1/8`
- **Hlavní rozhraní (eth0):** `192.168.0.2/24`
- **Docker rozhraní (docker0):** `172.17.0.1/16` (aktuálně neaktivní - `NO-CARRIER`)

---

## 5. Hlubší Analýza - Výsledky

Tato sekce obsahuje výsledky testů provedených na základě návrhu z předchozí kapitoly.

### 5.1. Systémové Limity a Omezení

- **Limity procesů (`ulimit -a`):**
  - **Otevřené soubory (`open files`):** 1024 (potenciální omezení pro aplikace s velkým počtem souborů).
  - **Čas CPU (`cpu time`):** Neomezený.
  - **Velikost paměti (`max memory size`):** Neomezená.
  - Ostatní limity jsou na standardních hodnotách.

- **Omezení `cgroups`:**
  - Prostředí využívá **cgroups v2**.
  - **Limit paměti (`memory.max`):** `max` (žádný specifický limit, omezeno pouze celkovou RAM).
  - **Limit CPU (`cpu.max`):** `max 100000` (žádné tvrdé omezení, pouze standardní řízení kvant).

- **Maximální doba běhu procesu:**
  - Testovací proces `sleep 3600 &` byl úspěšně spuštěn a monitorován. Nebyly zjištěny žádné krátkodobé limity.

### 5.2. Síťová Konektivita

- **Externí konektivita:** Plně funkční.
  - `ping 8.8.8.8`: Úspěšný, ICMP provoz je povolen.
  - `curl https://www.google.com`: Úspěšný, odchozí HTTPS (port 443) je povoleno.
- **Firewall:**
  - Zobrazení pravidel `iptables` vyžaduje root oprávnění a selhalo.
  - Základní odchozí komunikace je povolena, ale mohou existovat omezení pro jiné porty nebo příchozí spojení.

### 5.3. Dostupné Knihovny a Balíčky

- **Systémové sdílené knihovny:**
  - Získán kompletní seznam 422 knihoven z `/etc/ld.so.cache`.
- **Globální Python balíčky (`pip list`):**
  - Prostředí je čisté, obsahuje pouze základní balíčky.
- **Globální Node.js balíčky (`npm -g list`):**
  - K dispozici jsou klíčové vývojové nástroje: `npm`, `yarn`, `pnpm`, `jest`, `eslint`, `prettier`.

### 5.4. Oprávnění

- **Identita uživatele (`id`):**
  - Uživatel: `jules` (UID 1001)
  - Skupina: `jules` (GID 1001)
  - Členství: `sudo`
- **Oprávnění `sudo` (`sudo -l`):**
  - **`(ALL : ALL) ALL`** a **`NOPASSWD: ALL`**: Uživatel `jules` má plná, neomezená administrátorská oprávnění.

## 6. Celkový Závěr

Sandbox poskytuje flexibilní a výkonné prostředí s plnými administrátorskými právy. Hlavní potenciální omezení, na které je třeba si dát pozor, je **limit 1024 otevřených souborů na proces**. Ostatní zdroje (CPU, RAM, síť) se zdají být bez specifických tvrdých limitů, které by bránily běžnému vývoji.