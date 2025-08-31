from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from datetime import datetime, date

# V tej datoteki definiramo vse podatkovne modele, ki jih bomo uporabljali v aplikaciji.

# -----------------------------
# Uporabnik 
@dataclass_json
@dataclass
class Uporabnik:
    username: str = field(default="")
    role: str = field(default="")   # "student", "podjetje", "admin"
    password_hash: str = field(default="")
    last_login: datetime = field(default_factory=datetime.now)

@dataclass
class UporabnikDto:
    username: str = field(default="")
    role: str = field(default="")

# -----------------------------
# Študent
@dataclass_json
@dataclass
class Student:
    username: str = field(default="")    # povezava na Uporabnik
    ime: str = field(default="")
    priimek: str = field(default="")
    kontakt_tel: str = field(default="")
    povprecna_ocena: float = field(default=0.0)
    univerza: str = field(default="")

@dataclass_json
@dataclass
class StudentDto:
    ime: str = field(default="")
    priimek: str = field(default="")
    kontakt_tel: str = field(default="")
    povprecna_ocena: float = field(default=0.0)
    univerza: str = field(default="")

# -----------------------------
# Podjetje
@dataclass_json
@dataclass
class Podjetje:
    username: str = field(default="")   # povezava na Uporabnik
    ime: str = field(default="") 
    sedez: str = field(default="") 
    kontakt_mail: str = field(default="")

@dataclass_json
@dataclass
class PodjetjeDto:
    ime: str = field(default="")
    kontakt_mail: str = field(default="")
    sedez: str = field(default="")
    st_pripravnistev: int = field(default=0)  # število pripravništev, ki jih ima podjetje, JOIN na tabelo pripravnistvo

# -----------------------------
# Pripravništva
@dataclass_json
@dataclass
class Pripravnistvo:
    id: int = field(default=0)
    trajanje: int = field(default=0)   # v mesecih
    delovno_mesto: str = field(default="")
    opis_dela: str = field(default="")
    placilo: float = field(default=0.0)
    drzava: str = field(default="")
    kraj: str = field(default="")
    stevilo_mest: int = field(default=1)  # število prostih mest
    podjetje: str = field(default="")   # referenca na Podjetje

@dataclass_json
@dataclass
class PripravnistvoDto:
    id: int = field(default=0)
    trajanje: int = field(default=0)   # v mesecih
    delovno_mesto: str = field(default="")
    opis_dela: str = field(default="")
    placilo: float = field(default=0.0)
    drzava: str = field(default="")
    kraj: str = field(default="")
    stevilo_mest: int = field(default=1)  # število prostih mest
    podjetje: str = field(default=0)   # join na podjetje (ime podjetja)

# -----------------------------
# Prijave na pripravništva
@dataclass_json
@dataclass
class Prijava:
    id: int = field(default=0)
    status: str = field(default="") # npr. "v obravnavi", "odobrena", "zavrnjena"
    datum_prijave: date = field(default_factory=date.today)
    student: str = field(default="")     # referenca na Student
    pripravnistvo: int = field(default=0)  # referenca na Pripravnistvo

@dataclass_json
@dataclass
class PrijavaDto:
    student: str = field(default="")   # join na študenta (ime in priimek)
    podjetje: str = field(default="")  # join na podjetje (ime podjetja)
    pripravnistvo: str = field(default="")  # join na pripravništvo (delovno mesto)
    status: str = field(default="")
    datum_prijave: date = field(default_factory=date.today)