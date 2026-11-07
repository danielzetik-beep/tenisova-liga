# Tenisová liga táta & syn

Jednoduchá webová aplikace pro amatérský tenisový turnaj dvojic táta + syn.

## Funkce

- Registrace dvojice (jméno táty a syna), kdykoliv před rozlosováním, max 8 týmů
- Automatické rozlosování pavouka (při méně než 8 týmech dostanou některé dvojice volný los)
- Zadávání výsledku každého zápasu (skóre + datum, kdy se hrálo)
- Automatický postup vítěze do dalšího kola a zobrazení celkového vítěze
- Výsledek lze upravit nebo smazat, celý turnaj lze vymazat a začít znovu

## Spuštění

Potřeba je jen Python 3 (nic se neinstaluje):

```
python3 app.py
```

Aplikace poběží na `http://localhost:8000`. Data se ukládají do souboru `liga.db` ve stejné složce jako `app.py`.

## Dostupnost z více počítačů

Aby stránku viděli všichni kamarádi, spusťte aplikaci na počítači/serveru, který je dostupný ostatním (např. na vlastním serveru ve vaší síti nebo u libovolného hostování, které podporuje Python). Ostatní pak otevřou adresu toho stroje, např. `http://192.168.1.10:8000`.
