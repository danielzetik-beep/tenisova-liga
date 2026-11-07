# Tenisová liga táta & syn

Jednoduchá webová aplikace pro amatérský tenisový turnaj dvojic táta + syn, formát ligy – každý hraje s každým.

## Funkce

- Registrace dvojice (jméno táty a syna), max 8 týmů – při 8 týmech je turnaj plný
- Vytvoření zápasů „každý s každým" (u 8 týmů 28 zápasů)
- Zadávání výsledku: 2 sety (gemy) + při stavu 1:1 na sety výsledek tie-breaku, plus datum zápasu
- Tabulka: pořadí podle bodů (2 za výhru), pak rozdíl setů a rozdíl gemů
- Výsledek lze upravit nebo smazat, celý turnaj lze vymazat a začít znovu

## Spuštění

Potřeba je jen Python 3 (nic se neinstaluje):

```
python3 app.py
```

Aplikace poběží na `http://localhost:8000` (port lze změnit proměnnou prostředí `PORT`, např. `PORT=8899 python3 app.py`). Data se ukládají do souboru `liga.db` ve stejné složce jako `app.py`.

## Dostupnost z více počítačů

Aby stránku viděli všichni kamarádi, spusťte aplikaci na počítači/serveru, který je dostupný ostatním (např. na vlastním serveru ve vaší síti nebo u libovolného hostování, které podporuje Python). Ostatní pak otevřou adresu toho stroje, např. `http://192.168.1.10:8000`.
