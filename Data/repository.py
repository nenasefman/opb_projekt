import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
import Data.auth_public as auth
import os
from typing import List

from Data.models import (
    Uporabnik, Prijava, Pripravnistvo, PripravnistvoDto,
    Student, StudentDto, Podjetje, PodjetjeDto, PrijavaDto
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
        self.cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # ---------------- Uporabniki ----------------
    def dobi_uporabnika(self, username: str) -> Uporabnik:
        self.cur.execute("""
            SELECT username, role, password_hash, last_login
            FROM uporabniki
            WHERE username = %s
        """, (username,))
        u = Uporabnik.from_dict(self.cur.fetchone())
        return u

    def dodaj_uporabnika(self, uporabnik: Uporabnik):
        self.cur.execute("""
            INSERT INTO uporabniki(username, role, password_hash, last_login)
            VALUES (%s, %s, %s, %s)
        """, (uporabnik.username, uporabnik.role, uporabnik.password_hash, uporabnik.last_login))
        self.conn.commit()

    def posodobi_uporabnika(self, uporabnik: Uporabnik):
        self.cur.execute("""
            UPDATE uporabniki
            SET last_login = %s
            WHERE username = %s
        """, (uporabnik.last_login, uporabnik.username))
        self.conn.commit()

    # ----------------- Študenti ----------------
    def dodaj_studenta(self, student: Student):
        self.cur.execute("""
            INSERT INTO student(emso, ime, priimek, kontakt, povprecna_ocena, univerza_id, username)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (student.emso, student.ime, student.priimek, student.kontakt,
              student.povprecna_ocena, student.univerza_id, student.username))
        self.conn.commit()

    def dobi_studenta(self, username: str) -> Student:
        self.cur.execute("""
            SELECT emso, ime, priimek, kontakt, povprecna_ocena, univerza_id, username
            FROM student
            WHERE username = %s
        """, (username,))
        s = self.cur.fetchone()
        return Student.from_dict(s) if s else None

    def dobi_studenta_dto(self, username: str) -> StudentDto:
        self.cur.execute("""
            SELECT s.emso, s.ime, s.priimek, u.ime_univerze AS univerza
            FROM student s
            JOIN univerza u ON s.univerza_id = u.id
            WHERE s.username = %s
        """, (username,))
        s = self.cur.fetchone()
        return StudentDto.from_dict(s) if s else None

    # ----------------- Podjetja ----------------
    def dodaj_podjetje(self, podjetje: Podjetje):
        self.cur.execute("""
            INSERT INTO podjetje(ime, sedez, kontakt, username)
            VALUES (%s, %s, %s, %s)
        """, (podjetje.ime, podjetje.sedez, podjetje.kontakt, podjetje.username))
        self.conn.commit()

    def dobi_podjetje(self, username: str) -> Podjetje:
        self.cur.execute("""
            SELECT id, ime, sedez, kontakt, username
            FROM podjetje
            WHERE username = %s
        """, (username,))
        p = self.cur.fetchone()
        return Podjetje.from_dict(p) if p else None

    def dobi_podjetje_dto(self, username: str) -> PodjetjeDto:
        self.cur.execute("""
            SELECT p.id, p.ime, p.kontakt, COUNT(pr.id) AS st_pripravnistev
            FROM podjetje p
            LEFT JOIN pripravnistvo pr ON pr.podjetje_id = p.id
            WHERE p.username = %s
            GROUP BY p.id, p.ime, p.kontakt
        """, (username,))
        r = self.cur.fetchone()
        return PodjetjeDto.from_dict(r) if r else None

    # ---------------- Pripravništva ----------------
    def dobi_vsa_pripravnistva(self) -> List[Pripravnistvo]:
        self.cur.execute("""
            SELECT id, delovno_mesto, trajanje, placilo, drzava, kraj, stevilo_mest, podjetje_id, podrocje_id
            FROM pripravnistvo
            ORDER BY trajanje DESC
        """)
        return [Pripravnistvo.from_dict(p) for p in self.cur.fetchall()]

    def dobi_pripravnistva_dto(self) -> List[PripravnistvoDto]:
        self.cur.execute("""
            SELECT p.id, p.delovno_mesto, p.trajanje, p.placilo, 
                   pod.ime AS podjetje, po.podrocje AS podrocje, p.stevilo_mest
            FROM pripravnistvo p
            JOIN podjetje pod ON p.podjetje_id = pod.id
            JOIN podrocje po ON p.podrocje_id = po.id
            ORDER BY p.trajanje DESC
        """)
        return [PripravnistvoDto.from_dict(p) for p in self.cur.fetchall()]

    def dobi_pripravnistvo(self, id: int) -> Pripravnistvo:
        self.cur.execute("""
            SELECT id, delovno_mesto, trajanje, placilo, drzava, kraj, stevilo_mest, podjetje_id, podrocje_id
            FROM pripravnistvo
            WHERE id = %s
        """, (id,))
        r = self.cur.fetchone()
        return Pripravnistvo.from_dict(r) if r else None

    def dodaj_pripravnistvo(self, p: Pripravnistvo):
        self.cur.execute("""
            INSERT INTO pripravnistvo(delovno_mesto, trajanje, placilo, drzava, kraj, stevilo_mest, podjetje_id, podrocje_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (p.delovno_mesto, p.trajanje, p.placilo, p.drzava, p.kraj,
              p.stevilo_mest, p.podjetje_id, p.podrocje_id))
        self.conn.commit()

    # ---------------- Prijave na pripravništva ----------------
    def dobi_prijave_uporabnika(self, student_emso: str) -> List[PrijavaDto]:
        self.cur.execute("""
            SELECT pr.id, pr.status, pr.datum, p.delovno_mesto
            FROM prijava pr
            JOIN pripravnistvo p ON pr.pripravnistvo_id = p.id
            WHERE pr.student_emso = %s
        """, (student_emso,))
        return [PrijavaDto.from_dict(pr) for pr in self.cur.fetchall()]

    def dodaj_prijavo(self, prijava: Prijava):
        self.cur.execute("""
            INSERT INTO prijava(status, datum, student_emso, pripravnistvo_id)
            VALUES (%s, %s, %s, %s)
        """, (prijava.status, prijava.datum, prijava.student_emso, prijava.pripravnistvo_id))
        self.conn.commit()
    