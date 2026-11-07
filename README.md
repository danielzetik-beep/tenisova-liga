# Veteráni a naděje

Jednoduchá webová aplikace pro amatérskou tenisovou ligu párů rodič + dítě, formát ligy – každý hraje s každým.

## Funkce

- Registrace páru (jméno rodiče a dítěte), max 8 týmů – při 8 týmech je turnaj plný
- Vytvoření zápasů „každý s každým" (u 8 týmů 28 zápasů)
- Zadávání výsledku: 2 sety (gemy) + při stavu 1:1 na sety výsledek tie-breaku, plus datum zápasu
- Tabulka: pořadí podle bodů (2 za výhru), pak rozdíl setů a rozdíl gemů
- Výsledek lze upravit nebo smazat
- Admin sekce chráněná PINem (tlačítko 🔒 Admin): vytvoření zápasů, odebrání týmu a „vymazat vše“ vidí jen správce. Výchozí PIN je `TenisJahodnice`, změnit ho lze proměnnou prostředí `ADMIN_PIN` (lokálně např. `set ADMIN_PIN=mojeheslo` před `python app.py` na Windows; na PythonAnywhere přidejte řádek `os.environ["ADMIN_PIN"] = "vaseheslo"` do `wsgi.py`)

## Spuštění lokálně

Potřeba je jen Python 3 (nic se neinstaluje):

```
python3 app.py
```

Aplikace poběží na `http://localhost:8899` (port lze změnit proměnnou prostředí `PORT`, např. `PORT=8000 python3 app.py`). Data se ukládají do souboru `liga.db` ve stejné složce jako `app.py`.

## Dostupnost z více počítačů

### Rychle: jen ve stejné Wi-Fi síti

Spusťte aplikaci na počítači, který běží nonstop. Zjistěte jeho IP adresu (Windows: `ipconfig` → „IPv4 adresa“, např. 192.168.1.10) a kamarádi otevřou `http://192.168.1.10:8899`. Ve firewallu povolte Pythonu příchozí spojení na portu 8899.

### Veřejná adresa pro kohokoliv (z internetu)

Doporučeno: **PythonAnywhere** (zdarma, běží pořád, data `liga.db` jsou trvalá) na adrese `https://<vas-ucet>.pythonanywhere.com`:

1. Založte si free účet na pythonanywhere.com.
2. V konzoli **Bash** na PythonAnywhere stáhněte projekt: `git clone https://github.com/danielzetik-beep/tenisova-liga.git`
3. Jděte na záložku **Web** → **Add a new web app** → zvolte **Manual configuration** a verzi Pythonu 3.x.
4. U „Source code" zadejte cestu `/home/<vas-ucet>/tenisova-liga` a u „WSGI configuration file" cestu `/home/<vas-ucet>/tenisova-liga/wsgi.py` (nebo do výchozího WSGI souboru vložte obsah našeho `wsgi.py`).
5. Klikněte na **Reload** – stránka poběží na `https://<vas-ucet>.pythonanywhere.com`.
6. Volitelně změňte admin PIN: v souboru `wsgi.py` nahoře přidejte řádek `os.environ["ADMIN_PIN"] = "vaseheslo"` před `from app import ...`.

Alternativa: **Render** (zdarma, přímo z GitHubu) – New → Web Service → repozitář, Runtime Python 3, Start Command `python app.py`, Instance Type Free. Free varianta po ~15 min usíná a při restartu může `liga.db` smazat; PythonAnywhere je pro tento turnaj spolehlivější. Pro čistě lokální provoz použijte variantu výše (data zůstávají na vašem počítači).
