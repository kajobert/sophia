# Uživatelský Průvodce

Vítejte v projektu Sophia! Tento průvodce vás provede nejjednodušším způsobem, jak Sophii spustit a začít s ní komunikovat přes webové rozhraní.

## Předpoklady

- Nainstalovaný **Docker** a **Docker Compose**.
- Základní znalost příkazové řádky (terminálu).

## Spuštění Pomocí Docker Compose (Doporučená Metoda)

Toto je nejjednodušší a nejspolehlivější způsob, jak spustit celý ekosystém Sophie, včetně backendu, frontendu a všech potřebných služeb.

### Krok 1: Získání Projektu

Naklonujte si repozitář projektu z GitHubu na váš lokální počítač:
```bash
git clone <URL_REPOZITARE>
cd <NAZEV_SLOZKY_REPOZITARE>
```

### Krok 2: Konfigurace

Před prvním spuštěním je potřeba nastavit API klíč pro jazykový model Gemini.

1.  Najděte soubor `.env.example` v hlavním adresáři projektu.
2.  Zkopírujte ho a přejmenujte kopii na `.env`.
3.  Otevřete soubor `.env` a vložte svůj API klíč od Google Gemini:
    ```
    GEMINI_API_KEY=VASE_TAJNE_API_HESLO
    ```

### Krok 3: Spuštění Kontejnerů

V hlavním adresáři projektu spusťte následující příkaz. Docker Compose automaticky stáhne potřebné obrazy a spustí všechny služby.

```bash
docker-compose up --build
```

Tento příkaz může při prvním spuštění trvat několik minut, protože se stahují a sestavují všechny potřebné komponenty.

### Krok 4: Otevření Webového Rozhraní

Po úspěšném spuštění všech kontejnerů:

1.  Otevřete váš webový prohlížeč.
2.  Přejděte na adresu: `http://localhost:3000`

Měli byste vidět hlavní stránku webového rozhraní Sophie. Nyní můžete začít chatovat!

## Zastavení Aplikace

Pro zastavení všech běžících kontejnerů se vraťte do terminálu, kde jste spustili `docker-compose up`, a stiskněte `Ctrl + C`.

Pokud chcete kontejnery i smazat, použijte příkaz:
```bash
docker-compose down
```
