from Data.repository import Repo
from Data.models import *
from typing import List, Optional
from datetime import datetime

# V tej datoteki bomo definirali razred za obdelavo in prijavo na pripravništvo

class PripravnistvaService:
    def __init__(self) -> None:
        self.repo = Repo()          # Potrebovali bomo instanco repozitorija. Po drugi strani bi tako instanco 
                                    # lahko dobili tudi kot input v konstrukturju.

    # ---------------- Študenti ----------------
    def dobi_studenta(self, username: str) -> List[Student]:
        return self.repo.dobi_studenta(username)

    def dobi_studenta_dto(self, username: str) -> List[StudentDto]:
        return self.repo.dobi_studenta_dto(username)

    def dodaj_studenta(self, student: Student) -> None:
        self.repo.dodaj_studenta(student)

    def posodobi_studenta(self, student: Student) -> None:
        self.repo.posodobi_studenta(student)

    def izbrisi_studenta(self, username: str) -> None:
        self.repo.izbrisi_studenta(username)

    # ---------------- Podjetja ----------------
    def dobi_podjetje(self, username: str) -> Optional[Podjetje]:
        return self.repo.dobi_podjetje(username)

    def dobi_podjetje_dto(self, username: str) -> Optional[PodjetjeDto]:
        return self.repo.dobi_podjetje_dto(username)

    def dodaj_podjetje(self, podjetje: Podjetje) -> None:
        self.repo.dodaj_podjetje(podjetje)

    def posodobi_podjetje(self, podjetje: Podjetje) -> None:
        self.repo.posodobi_podjetje(podjetje)

    def izbrisi_podjetje(self, username: str) -> None:
        self.repo.izbrisi_podjetje(username)

    def dobi_vsa_podjetja_dto(self) -> List[PodjetjeDto]:
        return self.repo.dobi_vsa_podjetja_dto()

    # ---------------- Pripravništva ----------------
    def dobi_pripravnistvo(self, id: int) -> Optional[Pripravnistvo]:
        return self.repo.dobi_pripravnistvo(id)

    def dobi_pripravnistvo_dto(self, id: int) -> Optional[PripravnistvoDto]:
        return self.repo.dobi_pripravnistvo_dto(id)

    def dobi_vsa_pripravnistva(self) -> List[Pripravnistvo]:
        return self.repo.dobi_vsa_pripravnistva()

    def dobi_vsa_pripravnistva_dto(self) -> List[PripravnistvoDto]:
        return self.repo.dobi_vsa_pripravnistva_dto()

    def dodaj_pripravnistvo(self, pripravnistvo: Pripravnistvo) -> None:
        self.repo.dodaj_pripravnistvo(pripravnistvo)

    def posodobi_pripravnistvo(self, pripravnistvo: Pripravnistvo) -> None:
        self.repo.posodobi_pripravnistvo(pripravnistvo)

    def izbrisi_pripravnistvo(self, id: int) -> None:
        self.repo.izbrisi_pripravnistvo(id)

    # ---------------- Prijave ----------------
    def dobi_prijave_studenta(self, username: str) -> List[Prijava]:
        return self.repo.dobi_prijave_studenta(username)

    def dobi_prijave_studenta_dto(self, username: str) -> List[PrijavaDto]:
        return self.repo.dobi_prijave_studenta_dto(username)

    def dobi_prijave_na_pripravnistvo(self, id: int) -> List[Prijava]:
        return self.repo.dobi_prijave_na_pripravnistvo(id)

    def dobi_prijave_na_pripravnistvo_dto(self, id: int) -> List[PrijavaDto]:
        return self.repo.dobi_prijave_na_pripravnistvo_dto(id)

    def dobi_prijave_podjetja(self, username: str) -> List[Prijava]:
        return self.repo.dobi_prijave_podjetja(username)

    def dobi_prijave_podjetja_dto(self, username: str) -> List[PrijavaDto]:
        return self.repo.dobi_prijave_podjetja_dto(username)

    def posodobi_prijavo(self, prijava: Prijava) -> None:
        self.repo.posodobi_prijavo(prijava)
