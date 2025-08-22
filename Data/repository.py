import psycopg2, psycopg2.extensions, psycopg2.extras
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
import Data.auth_public as auth
import os
from typing import List

from Data.models import Uporabnik, UporabnikDto, Prijava, Pripravnistvo, PripravnistvoDto

# Preberemo port za bazo iz okoljskih spremenljivk
DB_PORT = os.environ.get('POSTGRES_PORT', 5432)

# V tej datoteki bomo implementirali razred Repo, ki bo vseboval metode za delo z bazo.


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

    # ---------------- Pripravništva ----------------
    def dobi_vsa_pripravnistva(self) -> List[Pripravnistvo]:
        self.cur.execute("""
            SELECT id, delovno_mesto, trajanje, placilo, drzava, kraj, stevilo_mest, podjetje_id, podrocje_id
            FROM pripravnistvo
            Order by trajanje DESC             
        """)
        pripravnistva =[Pripravnistvo.from_dict(p) for p in self.cur.fetchall()]
        return pripravnistva
    
    def dobi_pripravnistva_dto(self) -> List[PripravnistvoDto]:
        self.cur.execute("""
            SELECT p.id, p.delovno_mesto, p.trajanje, p.placilo, 
                   podjetje.ime as podjetje, podrocje.podrocje as podrocje, p.stevilo_mest
            FROM pripravnistvo p
            JOIN podjetje ON p.podjetje_id = podjetje.id
            JOIN podrocje ON p.podrocje_id = podrocje.id
            ORDER BY p.trajanje DESC
        """)
        pripravnistva_dto = [PripravnistvoDto.from_dict(p) for p in self.cur.fetchall()]
        return pripravnistva_dto
    
    def dobi_pripravnistvo(self, id: int) -> Pripravnistvo:
        self.cur.execute("""
            SELECT id, delovno_mesto, trajanje, placilo, drzava, kraj, stevilo_mest, podjetje_id, podrocje_id
            FROM pripravnistvo
            WHERE id = %s
        """, (id,))
        p = Pripravnistvo.from_dict(self.cur.fetchone())
        return p
    
    def dodaj_pripravnistvo(self, p: Pripravnistvo):
        self.cur.execute("""
            INSERT INTO pripravnistvo(delovno_mesto, trajanje, placilo, drzava, kraj, stevilo_mest)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (p.delovno_mesto, p.trajanje, p.placilo, p.drzava, p.kraj, p.stevilo_mest))
        self.conn.commit()

    # ---------------- Prijave na pripravništva ----------------
    def dobi_prijave_uporabnika(self, username: str) -> List[Prijava]:
        self.cur.execute("""
            SELECT id, uporabnik, pripravnistvo_id, datum, status
            FROM prijava
            WHERE uporabnik = %s
        """, (username,))
        prijava = [Prijava.from_dict(pr) for pr in self.cur.fetchall()]
        return prijava
    
#rabiva še: dodaj prijavo, posodobi (status) prijave, verjetno tudi dodaj podjetje in dodaj studenta am to nevem kako nardis ker sva itak ze dodali uporabnika ??
