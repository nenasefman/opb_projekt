CREATE TABLE Uporabnik (
    username TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('student', 'podjetje', 'admin')),
    password_hash TEXT NOT NULL,
    last_login TIMESTAMP);

CREATE TABLE Podjetje (
    username TEXT PRIMARY KEY,
	ime TEXT NOT NULL,
    sedez TEXT NOT NULL,
    kontakt_mail TEXT NOT NULL,
	FOREIGN KEY (username) REFERENCES Uporabnik(username));

CREATE TABLE Student (
    username TEXT PRIMARY KEY,
	ime TEXT NOT NULL,
    priimek TEXT NOT NULL,
    kontakt_tel INTEGER NOT NULL,
	povprecna_ocena FLOAT CHECK (povprecna_ocena >= 0 AND povprecna_ocena <= 10),
    univerza TEXT NOT NULL,
	FOREIGN KEY (username) REFERENCES Uporabnik(username));

CREATE TABLE Pripravnistvo (
    id SERIAL PRIMARY KEY,
    trajanje INTEGER NOT NULL CHECK (trajanje >= 0),
	delovno_mesto TEXT NOT NULL,
	opis_dela TEXT NOT NULL,
    placilo FLOAT NOT NULL CHECK (placilo >= 0),
	drzava TEXT NOT NULL,
	kraj TEXT NOT NULL,
	stevilo_mest INT NOT NULL CHECK (stevilo_mest > 0),
    podjetje TEXT REFERENCES Podjetje(username) ON DELETE CASCADE);

CREATE TABLE Prijava (
    id SERIAL PRIMARY KEY,
    status TEXT NOT NULL CHECK (status IN ('v obravnavi', 'odobrena', 'zavrnjena')),
    datum_prijave DATE NOT NULL DEFAULT CURRENT_DATE,
    student TEXT REFERENCES Student(username) ON DELETE CASCADE,
    pripravnistvo_id INT REFERENCES Pripravnistvo(id) ON DELETE CASCADE);
