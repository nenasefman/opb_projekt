
from Data.repository import Repo
from Data.models import *
import bcrypt
from datetime import date
from typing import Union


class AuthService:
    repo : Repo
    def __init__(self):
         self.repo = Repo()


    def obstaja_uporabnik(self, uporabnik: str) -> bool:
        '''Preveri, če uporabnik obstaja v bazi.'''
        try:
            user = self.repo.dobi_uporabnika(uporabnik)
            return True
        except:
            return False
        

    def dodaj_uporabnika(self, uporabnik: str, rola: str, geslo: str) -> UporabnikDto:
        '''Doda novega uporabnika v bazo.'''
        
        # zgradimo hash za geslo od uporabnika
        bytes = geslo.encode('utf-8')                   # geso zakodiramo kot seznam bytov
        salt = bcrypt.gensalt()                         # ustvarimo "salt" za hash
        password_hash = bcrypt.hashpw(bytes, salt)      # ustvarimo hash gesla


        # ustvarimo objekt Uporabnik in ga zapišemo bazo
        u = Uporabnik(
            username=uporabnik,
            role=rola,
            password_hash=password_hash.decode(),
            last_login= date.today().isoformat()
        )

        self.repo.dodaj_uporabnika(u)

        return UporabnikDto(username=uporabnik, role=rola)
    

    def prijavi_uporabnika(self, uporabnik : str, geslo: str) -> Union[UporabnikDto, bool]:
        '''Preveri, če sta uporabnik in geslo pravilna. Če sta, vrne UporabnikDto, sicer False.'''

        # dobimo uporabnika iz baze
        user = self.repo.dobi_uporabnika(uporabnik)

        geslo_bytes = geslo.encode('utf-8')
        # Ustvarimo hash iz gesla, ki ga je vnesel uporabnik
        succ = bcrypt.checkpw(geslo_bytes, user.password_hash.encode('utf-8'))

        if succ:
            # popravimo last login time
            user.last_login = date.today().isoformat()
            self.repo.posodobi_uporabnika(user)
            return UporabnikDto(username=user.username, role=user.role)
        
        return False
    

    def dobi_uporabnika(self, username: str) -> Uporabnik:
        '''Vrne uporabnika z danim uporabniškim imenom.'''
        return self.repo.dobi_uporabnika(username)