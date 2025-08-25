CREATE TABLE Podjetje (
    id INTEGER PRIMARY KEY,
	ime TEXT NOT NULL,
    sedez TEXT NOT NULL,
    kontakt TEXT NOT NULL);

CREATE TABLE Univerza (
    id INTEGER PRIMARY KEY,
	ime_univerze TEXT NOT NULL,
    fakulteta TEXT NOT NULL,
    kontakt TEXT NOT NULL);

CREATE TABLE Podrocje (
    id INTEGER PRIMARY KEY,
	podrocje TEXT NOT NULL,
    veja TEXT NOT NULL);

CREATE TABLE Student (
    emso VARCHAR(13) PRIMARY KEY,
	ime TEXT NOT NULL,
    priimek TEXT NOT NULL,
    kontakt INTEGER NOT NULL,
	povprecna_ocena FLOAT CHECK (povprecna_ocena >= 0 AND povprecna_ocena <= 10),
    univerza_id INT REFERENCES Univerza(id) ON DELETE CASCADE);

CREATE TABLE Pripravnistvo (
    id INTEGER PRIMARY KEY,
	delovno_mesto TEXT NOT NULL,
    trajanje INTEGER NOT NULL CHECK (trajanje >= 0),
    placilo FLOAT NOT NULL CHECK (placilo >= 0),
	drzava TEXT NOT NULL,
	kraj TEXT NOT NULL,
	stevilo_mest INT NOT NULL CHECK (stevilo_mest >= 0),
    podjetje_id INT REFERENCES Podjetje(id) ON DELETE CASCADE,
    podrocje_id INT REFERENCES Podrocje(id) ON DELETE CASCADE);

CREATE TABLE Prijava (
    id SERIAL PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('v obravnavi', 'odobrena', 'zavrnjena')),
    datum DATE NOT NULL DEFAULT CURRENT_DATE,
    student_emso VARCHAR(13) REFERENCES Student(emso) ON DELETE CASCADE,
    pripravnistvo_id INT REFERENCES Pripravnistvo(id) ON DELETE CASCADE);

CREATE TABLE Uporabnik (
    username TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    last_login TIMESTAMP);
    role TEXT NOT NULL CHECK (role IN ('student', 'podjetje', 'admin')),

CREATE TABLE IF NOT EXISTS Registracija (
    uporabnisko_ime TEXT PRIMARY KEY,
    uporabnisko_geslo TEXT NOT NULL);


-- js bi to mal drgač: ne rabva pomojem posebi registracije ampak sam uporabnik in pol
-- k uporabnik napiše not username geslo pa role izpolne se dodatne podatke glede na to a
-- je podjetje al student in pol se linka uporabnik na eno izmed teh dveha tabel kamor se 
-- pol shranjujejo dejanski podatki od folka


-- 1) Odstranimo nepotrebno tabelo Registracija
DROP TABLE IF EXISTS Registracija;

-- 2) Dodamo povezave iz Student in Podjetje na Uporabnik
ALTER TABLE Student 
ADD COLUMN username TEXT UNIQUE REFERENCES Uporabnik(username) ON DELETE CASCADE;

ALTER TABLE Podjetje 
ADD COLUMN username TEXT UNIQUE REFERENCES Uporabnik(username) ON DELETE CASCADE;
