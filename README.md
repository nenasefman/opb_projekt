# pripravništvo_najdi.si

Avtorji: Nena Šefman Hodnik in Zala Gregorc

## O projektu

pripravništvo_najdi.si je spletna aplikacija, razvita kot del projekta pri predmetu *Podatkovne baze*, katere namen je povezati študente v iskanju pripravništev s podjetji, ki iščejo mlade talente.

### Za študente

Si tik pred diplomo, bogat z znanjem, a brez praktičnih izkušenj?  
Aplikacija pripravništvo_najdi.si ti omogoča:

- iskanje plačanih in neplačanih pripravništev po vsem svetu,
- filtriranje pripravništev glede na področje, lokacijo in trajanje,
- oddajo prijave neposredno preko spletnega vmesnika.

### Za podjetja

Predstavljaš podjetje, ki želi pritegniti perspektivne študente?  
S prijavo v aplikacijo lahko:

- ustvariš aktivno pripravništvo,
- pregledaš prejete prijave,
- hitro najdeš ustrezne kandidate glede na tvoje potrebe.

---
### Tehnične podorbnosti 

Aplikacija je razvita v programskem jeziku Python z uporabo Bottle frameworka, ki skrbi za usmerjanje zahtevkov, obdelavo HTTP metod in povezovanje s predlogami. Za oblikovanje uporabniškega vmesnika je uporabljen TailwindCSS, ki omogoča odziven in estetski dizajn brez kompleksnega CSS-ja. Podatki so shranjeni v PostgreSQL bazi. Projekt sestavljajo štiri mape. Prva "Baza" vsebuje kodo za ustvarjanje tabel v podatkovni bazi in dostop do njih. Naslednja je "Data", ki skrbi za dostop do baze. "Services" je za uvoz podatkov in  "Presentation/views" pa vsebujejo HTML template-e za prikaz podatkov uporabniku.


---

## ER diagram
<img width="2409" height="920" alt="Blank diagram-2" src="https://github.com/user-attachments/assets/1d0dbc52-7ec1-493f-8303-eaad710771f8" />

