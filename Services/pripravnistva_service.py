from Data.repository import Repo
from Data.models import *
from typing import List, Optional
from datetime import datetime

class PripravnistvaService:
    def __init__(self) -> None:
        self.repo = Repo()
    
    # ---------------- Študenti ----------------
    
    def dobi_studenta(self, emso: str) -> Optional[Student]:
        return self.repo.dobi_studenta(emso)

    def dobi_studente(self) -> List[Student]:
        return self.repo.dobi_studente()

    def dobi_studente_dto(self) -> List[StudentDto]:
        return self.repo.dobi_studente_dto()

    def dodaj_studenta(self, student: Student) -> None:
        self.repo.dodaj_studenta(student)

    def posodobi_studenta(self, student: Student) -> None:
        self.repo.posodobi_studenta(student)

    def izbrisi_studenta(self, emso: str) -> None:
        self.repo.izbrisi_studenta(emso)
    

    # ---------------- Prijave na pripravništva ----------------

    def dobi_prijave_studenta(self, emso: str) -> List[PrijavaDto]:
        return self.repo.dobi_prijave_studenta(emso)

    def dobi_prijave_na_pripravnistvo(self, pripravnistvo_id: int) -> List[PrijavaDto]:
        return self.repo.dobi_prijave_na_pripravnistvo(pripravnistvo_id)

    def oddaj_prijavo(self, prijava: Prijava) -> None:
        prijava.cas_prijave = datetime.now()
        self.repo.dodaj_prijavo(prijava)

    def izbrisi_prijavo(self, prijava_id: int) -> None:
        self.repo.izbrisi_prijavo(prijava_id)


    # ---------------- Pripravništva ----------------
    
    def dobi_pripravnistva(self) -> List[Pripravnistvo]:
        return self.repo.dobi_pripravnistva()
    
    def dobi_pripravnistva_dto(self) -> List[PripravnistvoDto]:
        return self.repo.dobi_pripravnistva_dto()

    def dobi_pripravnistvo(self, id: int) -> Optional[Pripravnistvo]:
        return self.repo.dobi_pripravnistvo(id)

    def dodaj_pripravnistvo(self, pripravnistvo: Pripravnistvo) -> None:
        self.repo.dodaj_pripravnistvo(pripravnistvo)

    def posodobi_pripravnistvo(self, pripravnistvo: Pripravnistvo) -> None:
        self.repo.posodobi_pripravnistvo(pripravnistvo)

    def izbrisi_pripravnistvo(self, id: int) -> None:
        self.repo.izbrisi_pripravnistvo(id)


    # ---------------- Podjetja ----------------
    
    def dobi_podjetje(self, username: str) -> Optional[Podjetje]:
        return self.repo.dobi_podjetje(username)

    def dobi_podjetja(self) -> List[Podjetje]:
        return self.repo.dobi_podjetja()

    def dobi_podjetja_dto(self) -> List[PodjetjeDto]:
        return self.repo.dobi_podjetja_dto()

    def dodaj_podjetje(self, podjetje: Podjetje) -> None:
        self.repo.dodaj_podjetje(podjetje)

    def posodobi_podjetje(self, podjetje: Podjetje) -> None:
        self.repo.posodobi_podjetje(podjetje)

    def izbrisi_podjetje(self, username: str) -> None:
        self.repo.izbrisi_podjetje(username)
