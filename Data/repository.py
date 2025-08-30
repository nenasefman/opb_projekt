import psycopg2, psycopg2.extensions, psycopg2.extras
from Data import auth_public as auth
import os
from typing import List

from .models import (
    Uporabnik, Student, StudentDto, Podjetje, PodjetjeDto,
    Pripravnistvo, PripravnistvoDto, Prijava, PrijavaDto
)

# Preberemo port za bazo iz okoljskih spremenljivk
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)


class Repo:
    def __init__(self):
        self.conn = psycopg2.connect(
            database=auth.db,
            host=auth.host,
            user=auth.user,
            password=auth.password,
            port=DB_PORT
        )
        self.conn.set_client_encoding('UTF8')
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # ---------------- Uporabniki ----------------
    def dobi_uporabnika(self, username: str) -> Uporabnik:
        self.cur.execute("""
            SELECT username, role, password_hash, last_login
            FROM uporabnik
            WHERE username = %s
        """, (username,))
        u = self.cur.fetchone()
        return Uporabnik.from_dict(u) if u else None

    def dodaj_uporabnika(self, uporabnik: Uporabnik):
        try:
            self.cur.execute("""
                INSERT INTO uporabnik(username, role, password_hash, last_login)
                VALUES (%s, %s, %s, %s)
            """, (uporabnik.username, uporabnik.role, uporabnik.password_hash, uporabnik.last_login))
            self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            raise ValueError("Uporabnik s tem uporabniškim imenom že obstaja.")
        except Exception as e:
            self.conn.rollback()
            print(f"Napaka pri dodajanju uporabnika: {e}")
            raise e

    def posodobi_uporabnika(self, uporabnik: Uporabnik):
        self.cur.execute("""
            UPDATE uporabnik
            SET last_login = %s
            WHERE username = %s
        """, (uporabnik.last_login, uporabnik.username))
        self.conn.commit()

    # ----------------- Študenti ----------------
    def dodaj_studenta(self, student: Student):
        # Preverimo, ali obstaja uporabnik
        self.cur.execute("SELECT username FROM uporabnik WHERE username = %s", (student.username,))
        if not self.cur.fetchone():
            raise ValueError("Uporabnik s tem uporabniškim imenom ne obstaja, ne moremo dodati študenta.")

        try:
            self.cur.execute("""
                INSERT INTO student(username, ime, priimek, kontakt_tel, povprecna_ocena, univerza)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (student.username, student.ime, student.priimek, student.kontakt_tel, student.povprecna_ocena, student.univerza))
            self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            raise ValueError("Študent s tem uporabniškim imenom že obstaja.")

    def dobi_studenta(self, username: str) -> Student:
        self.cur.execute("""
            SELECT username, ime, priimek, kontakt_tel, povprecna_ocena, univerza
            FROM student
            WHERE username = %s
        """, (username,))
        s = self.cur.fetchone()
        return Student.from_dict(s) if s else None

    def dobi_studenta_dto(self, username: str) -> StudentDto:
        self.cur.execute("""
            SELECT ime, priimek, kontakt_tel, povprecna_ocena, univerza
            FROM student
            WHERE username = %s
        """, (username,))
        row = self.cur.fetchone()
        return StudentDto.from_dict(row) if row else None

    def posodobi_studenta(self, student: Student):
        '''
        Posodobi podatke o študentu. Če je katero od polj None, se to polje ne spremeni.
        '''
        stari = self.dobi_studenta(student.username)
        if not stari:
            raise ValueError("Študent ne obstaja.")

        try:
            self.cur.execute("""
                UPDATE student
                SET ime = %s, priimek = %s, kontakt_tel = %s,
                    povprecna_ocena = %s, univerza = %s
                WHERE username = %s
            """, (
                student.ime or stari.ime,
                student.priimek or stari.priimek,
                student.kontakt_tel or stari.kontakt_tel,
                student.povprecna_ocena or stari.povprecna_ocena,
                student.univerza or stari.univerza,
                student.username
            ))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Napaka pri posodobitvi študenta: {e}")
            raise e
    
    def izbrisi_studenta(self, username: str):
        self.cur.execute("""
            DELETE FROM student
            WHERE username = %s
        """, (username,))
        self.conn.commit()

    # ----------------- Podjetja ----------------
    def dodaj_podjetje(self, podjetje: Podjetje):
        # Preverimo, ali obstaja uporabnik
        self.cur.execute("SELECT username FROM uporabnik WHERE username = %s", (podjetje.username,))
        if not self.cur.fetchone():
            raise ValueError("Uporabnik s tem uporabniškim imenom ne obstaja, ne moremo dodati podjetja.")

        try:
            self.cur.execute("""
                INSERT INTO podjetje(username, ime, sedez, kontakt_mail)
                VALUES (%s, %s, %s, %s)
            """, (podjetje.username, podjetje.ime, podjetje.sedez, podjetje.kontakt_mail))
            self.conn.commit()
        except psycopg2.IntegrityError:
            self.conn.rollback()
            raise ValueError("Podjetje s tem uporabniškim imenom že obstaja.")


    def dobi_podjetje(self, username: str) -> Podjetje:
        self.cur.execute("""
            SELECT username, ime, sedez, kontakt_mail
            FROM podjetje
            WHERE username = %s
        """, (username,))
        p = self.cur.fetchone()
        return Podjetje.from_dict(p) if p else None

    def dobi_podjetje_dto(self, username: str) -> PodjetjeDto:
        self.cur.execute("""
            SELECT p.ime, p.kontakt_mail, p.sedez,
                COUNT(pr.id) AS st_pripravnistev
            FROM podjetje p
            LEFT JOIN pripravnistvo pr 
                ON pr.podjetje = p.username
            WHERE p.username = %s
            GROUP BY p.ime, p.kontakt_mail, p.sedez
        """, (username,))
        row = self.cur.fetchone()
        return PodjetjeDto.from_dict(row) if row else None
    
    def dobi_vsa_podjetja_dto(self) -> List[PodjetjeDto]:
        self.cur.execute("""
            SELECT p.ime, p.kontakt_mail, p.sedez,
                COUNT(pr.id) AS st_pripravnistev
            FROM podjetje p
            LEFT JOIN pripravnistvo pr 
                ON pr.podjetje = p.username
            GROUP BY p.ime, p.kontakt_mail, p.sedez
            ORDER BY p.ime
        """)
        rows = self.cur.fetchall()
        return [PodjetjeDto.from_dict(r) for r in rows]
    
    def posodobi_podjetje(self, podjetje: Podjetje):
        '''
        Posodobi podatke o podjetju. Če je katero od polj None, se to polje ne spremeni.
        '''
        staro = self.dobi_podjetje(podjetje.username)
        if not staro:
            raise ValueError("Podjetje ne obstaja.")

        try:
            self.cur.execute("""
                UPDATE podjetje
                SET ime = %s,
                    sedez = %s,
                    kontakt_mail = %s
                WHERE username = %s
            """, (
                podjetje.ime or staro.ime,
                podjetje.sedez or staro.sedez,
                podjetje.kontakt_mail or staro.kontakt_mail,
                podjetje.username
            ))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Napaka pri posodobitvi podjetja: {e}")
            raise e
    
    def izbrisi_podjetje(self, username: str):
        self.cur.execute("""
            DELETE FROM podjetje
            WHERE username = %s
        """, (username,))
        self.conn.commit()

    # ---------------- Pripravništva ----------------
    def dobi_vsa_pripravnistva(self) -> List[Pripravnistvo]:
        self.cur.execute("""
            SELECT id, trajanje, delovno_mesto, opis_dela,  placilo, drzava, kraj, stevilo_mest, podjetje
            FROM pripravnistvo
            ORDER BY trajanje DESC
        """)
        return [Pripravnistvo.from_dict(p) for p in self.cur.fetchall()]

    def dobi_vsa_pripravnistva_dto(self) -> List[PripravnistvoDto]:
        self.cur.execute("""
            SELECT pr.id, pr.trajanje, pr.delovno_mesto, pr.opis_dela, pr.placilo, pr.drzava, pr.kraj, pr.stevilo_mest, p.ime AS podjetje
            FROM pripravnistvo pr
            JOIN podjetje p ON pr.podjetje = p.username
            ORDER BY pr.trajanje DESC
        """)
        return [PripravnistvoDto.from_dict(p) for p in self.cur.fetchall()]

    def dobi_pripravnistvo(self, id: int) -> Pripravnistvo:
        self.cur.execute("""
            SELECT id, trajanje, delovno_mesto, opis_dela,  placilo, drzava, kraj, stevilo_mest, podjetje
            FROM pripravnistvo
            WHERE id = %s
        """, (id,))
        r = self.cur.fetchone()
        return Pripravnistvo.from_dict(r) if r else None
    
    def dobi_pripravnistvo_dto(self, id: int) -> PripravnistvoDto:
        self.cur.execute("""
            SELECT pr.id, pr.trajanje, pr.delovno_mesto, pr.opis_dela, pr.placilo, pr.drzava, pr.kraj, pr.stevilo_mest, p.ime AS podjetje
            FROM pripravnistvo pr
            JOIN podjetje p ON pr.podjetje = p.username
            WHERE pr.id = %s
        """, (id,))
        r = self.cur.fetchone()
        return PripravnistvoDto.from_dict(r) if r else None

    def dodaj_pripravnistvo(self, pripravnistvo: Pripravnistvo):
        self.cur.execute("""
            INSERT INTO pripravnistvo(trajanje, delovno_mesto, opis_dela, placilo, drzava, kraj, stevilo_mest, podjetje)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (pripravnistvo.trajanje, pripravnistvo.delovno_mesto, pripravnistvo.opis_dela, pripravnistvo.placilo, pripravnistvo.drzava, pripravnistvo.kraj, pripravnistvo.stevilo_mest, pripravnistvo.podjetje))
        self.conn.commit()
    
    def posodobi_pripravnistvo(self, pripravnistvo: Pripravnistvo):
        '''
        Posodobi podatke o pripravništvu. Če je katero od polj None, se to polje ne spremeni.
        '''
        staro = self.dobi_pripravnistvo(pripravnistvo.id)
        if not staro:
            raise ValueError("Pripravništvo ne obstaja.")

        try:
            self.cur.execute("""
                UPDATE pripravnistvo
                SET trajanje = %s,
                    delovno_mesto = %s,
                    opis_dela = %s,
                    placilo = %s,
                    drzava = %s,
                    kraj = %s,
                    stevilo_mest = %s,
                    podjetje = %s
                WHERE id = %s
            """, (
                pripravnistvo.trajanje or staro.trajanje,
                pripravnistvo.delovno_mesto or staro.delovno_mesto,
                pripravnistvo.opis_dela or staro.opis_dela,
                pripravnistvo.placilo or staro.placilo,
                pripravnistvo.drzava or staro.drzava,
                pripravnistvo.kraj or staro.kraj,
                pripravnistvo.stevilo_mest or staro.stevilo_mest,
                pripravnistvo.podjetje or staro.podjetje,
                pripravnistvo.id
            ))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Napaka pri posodobitvi pripravništva: {e}")
            raise e
    
    def izbrisi_pripravnistvo(self, id: int):
        self.cur.execute("""
            DELETE FROM pripravnistvo
            WHERE id = %s
        """, (id,))
        self.conn.commit()

    # ---------------- Prijave na pripravništva ----------------
    def dobi_prijave_studenta(self, username: str) -> List[Prijava]:
        """Vrne vse prijave, ki jih je študent oddal."""
        self.cur.execute("""
            SELECT id, status, datum_prijave, student, pripravnistvo
            FROM prijava
            WHERE student = %s
        """, (username,))
        return [Prijava.from_dict(r) for r in self.cur.fetchall()]
    
    def dobi_prijave_studenta_dto(self, username: str) -> List[PrijavaDto]:
        """Vrne vse prijave določenega študenta v DTO obliki (student, podjetje, pripravništvo)."""
        self.cur.execute("""
            SELECT stud.ime || ' ' || stud.priimek AS student,
                   pod.ime AS podjetje,
                   pripr.delovno_mesto AS pripravnistvo,
                   prij.status,
                   prij.datum_prijave
            FROM prijava prij
            JOIN student stud ON prij.student = stud.username
            JOIN pripravnistvo pripr ON prij.pripravnistvo_id = pripr.id
            JOIN podjetje pod ON pripr.podjetje = pod.username
            WHERE prij.student = %s
            ORDER BY prij.datum_prijave DESC
        """, (username,))
        return [PrijavaDto.from_dict(r) for r in self.cur.fetchall()]

    def dobi_prijave_na_pripravnistvo(self, id: int) -> List[Prijava]:
        """Vrne vse prijave za določeno pripravništvo."""
        self.cur.execute("""
            SELECT id, status, datum_prijave, student, pripravnistvo
            FROM prijava
            WHERE pripravnistvo = %s
            ORDER BY datum_prijave DESC
        """, (id,))
        return [Prijava.from_dict(r) for r in self.cur.fetchall()]

    def dobi_prijave_na_pripravnistvo_dto(self, id: int) -> List[PrijavaDto]:
        """Vrne vse prijave za določeno pripravništvo v DTO obliki (student, podjetje, pripravništvo)."""
        self.cur.execute("""
            SELECT stud.ime || ' ' || stud.priimek AS student,
                   pod.ime AS podjetje,
                   pripr.delovno_mesto AS pripravnistvo,
                   prij.status,
                   prij.datum_prijave
            FROM prijava prij
            JOIN student stud ON prij.student = stud.username
            JOIN pripravnistvo pripr ON prij.pripravnistvo_id = pripr.id
            JOIN podjetje pod ON pripr.podjetje = pod.username
            WHERE prij.pripravnistvo = %s
            ORDER BY prij.datum_prijave DESC
        """, (id,))
        return [PrijavaDto.from_dict(r) for r in self.cur.fetchall()]

    def dobi_prijave_podjetja(self, username: str) -> List[Prijava]:
        """Vrne vse prijave, ki so bile oddane za pripravništva tega podjetja."""
        self.cur.execute("""
            SELECT prij.id, prij.status, prij.datum_prijave, prij.student, prij.pripravnistvo
            FROM prijava prij
            JOIN pripravnistvo pripr ON prij.pripravnistvo_id = pripr.id
            WHERE pripr.podjetje = %s
            ORDER BY prij.datum_prijave DESC
        """, (username,))
        return [Prijava.from_dict(r) for r in self.cur.fetchall()]

    def dobi_prijave_podjetja_dto(self, username: str) -> List[PrijavaDto]:
        """Vrne vse prijave podjetja v DTO obliki (student, podjetje, pripravništvo)."""
        self.cur.execute("""
            SELECT stud.ime || ' ' || stud.priimek AS student,
                   pod.ime AS podjetje,
                   pripr.delovno_mesto AS pripravnistvo,
                   prij.status,
                   prij.datum_prijave
            FROM prijava prij
            JOIN student stud ON prij.student = stud.username
            JOIN pripravnistvo pripr ON prij.pripravnistvo_id = pripr.id
            JOIN podjetje pod ON pripr.podjetje = pod.username
            WHERE pod.username = %s
            ORDER BY prij.datum_prijave DESC
        """, (username,))
        return [PrijavaDto.from_dict(r) for r in self.cur.fetchall()]
    
    def posodobi_prijavo(self, prijava: Prijava):
        """
        Posodobi status obstoječe prijave. Če prijava ne obstaja, sproži ValueError.
        """
        self.cur.execute("SELECT id FROM prijava WHERE id = %s", (prijava.id,))
        if not self.cur.fetchone():
            raise ValueError("Prijava ne obstaja.")

        self.cur.execute("""
            UPDATE prijava
            SET status = %s
            WHERE id = %s
        """, (prijava.status, prijava.id))
        self.conn.commit()