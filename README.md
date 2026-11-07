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

Aplikace poběží na `http://localhost:8899` (port lze změnit proměnnou prostředí `PORT`, např. `PORT=8000 python3 app.py`). Data se ukládají do souboru `liga.db` ve stejné složce jako `app.py`.

## Dostupnost z více počítačů

### Rychle: jen ve stejné Wi-Fi síti

Spusťte aplikaci na počítači, který běží nonstop. Zjistěte jeho IP adresu (Windows: `ipconfig` → „IPv4 adresa“, např. 192.168.1.10) a kamarádi otevřou `http://192.168.1.10:8899`. Ve firewallu povolte Pythonu příchozí spojení na portu 8899.

### Veřejná adresa pro kohokoliv (z internetu)

Nasazení na Render (zdarma, přímo z GitHubu):

1. Na render.com se přihlaste účtem GitHub.
2. **New → Web Service** → připojte repozitář `danielzetik-beep/tenisova-liga`.
3. Runtime: **Python 3**, Start Command: `python app.py` (port nastaví Render sám přes proměnnou PORT).
4. Instance Type: **Free** → Create Web Service.
5. Po pár minutách dostanete veřejnou adresu, např. `https://tenisova-liga.onrender.com` – tu pošlete kamarádům.

Poznámka: free varianta Render po ~15 min nečinnosti usíná (první požadavek pak trvá pár sekund) a při restartu služby se soubor `liga.db` může vymazat – výsledky si případně poznamenejte, nebo zvažte placený/always-on plán. Pro čistě lokální provoz použijte variantu výše (data zůstávají na vašem počítači).
