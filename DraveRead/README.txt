DraveRead v0.1
==============

Voorlezer (tekst-naar-spraak) met natuurlijke, neurale stemmen via Neuvoice.
On-device: draait op je eigen pc, geen cloud.

BELANGRIJK - eerste keer
------------------------
- De eerste installatie haalt de stemmen-motor op (Neuvoice + ONNX Runtime);
  dat is wat groter, even geduld.
- De ALLEREERSTE keer dat je op Voorlezen klikt, worden de stem-modellen
  eenmalig gedownload (internet nodig). Daarna werkt voorlezen offline.

Starten
-------
- Dubbelklik run.bat (installeert zichzelf de eerste keer).
- Werkt het niet? start-debug.bat (toont de fout) of herstel.bat.

Gebruik
-------
- Plak/typ tekst of open een .txt. Kies Stem en Taal van de tekst
  (standaard Nederlands). Stel Snelheid en Kwaliteit in.
- Voorlezen / Pauze / Stop. Bij een nieuwe tekst maakt de app eerst de audio
  (dat duurt even, zeker bij hogere kwaliteit), daarna speelt het af.
- Opslaan als audio... bewaart het als .wav.

Stemmen: Alina, Cem, Cole, Giray, Leon, Lina, Linda, Mustafa, Sarp, Selin,
Sema, Soras. Talen: o.a. Nederlands, Engels, Duits, Frans, Spaans, en meer.

Een .exe maken (optioneel)
--------------------------
- run.bat (voor de .venv), daarna bouw-exe.bat -> dist\DraveRead\DraveRead.exe
  (map-versie; groot vanwege de stemmen-motor).

Contact / donatie
-----------------
service@dravenlock.nl - paypal.me/roger076
