from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from datetime import datetime

# V tej datoteki definiramo vse podatkovne modele, ki jih bomo uporabljali v aplikaciji.

# -----------------------------
@dataclass_json
@dataclass
class Podjetje:
    id: int = field(default=0) 
    ime: str = field(default="") 
    sedez: str = field(default="") 
    kontakt: str = field(default="") 

@dataclass_json
@dataclass
class PodjetjeDto:
    id: int = field(default=0)
    ime: str = field(default="")
    kontakt: str = field(default="")
    st_pripravnistev: int = field(default=0)  # število pripravništev, ki jih ima podjetje

# -----------------------------
@dataclass_json
@dataclass
class Student:
    emso: str = field(default="")
    ime: str = field(default="")
    priimek: str = field(default="")
    kontakt: str = field(default="")
    povprecna_ocena: float = field(default=0.0)
    univerza_id: int = field(default=0)  # referenca na tabelo Univezra


@dataclass_json
@dataclass
class StudentDto:
    emso: str = field(default="")
    ime: str = field(default="")
    priimek: str = field(default="")
    univerza: str = field(default="")  # join na Univerza

# -----------------------------
@dataclass_json
@dataclass
class Univerza:
    id: int = field(default=0)
    ime_univerze: str = field(default="")
    fakulteta: str = field(default="")
    kontakt: str = field(default="")


# -----------------------------
@dataclass_json
@dataclass
class Podrocje:
    id: int = field(default=0)
    podrocje: str = field(default="")
    veja: str = field(default="")

# -----------------------------
@dataclass_json
@dataclass
class Pripravnistvo:
    id: int = field(default=0)
    delovno_mesto: str = field(default="")
    trajanje: int = field(default=0)   # v mesecih
    placilo: float = field(default=0.0)
    drzava: str = field(default="")
    kraj: str = field(default="")
    stevilo_mest: int = field(default=0)
    podjetje_id: int = field(default=0)   # referenca na Podjetje
    podrocje_id: int = field(default=0)   # referenca na Podrocje

@dataclass_json
@dataclass
class PripravnistvoDto:
    id: int = field(default=0)
    delovno_mesto: str = field(default="")
    trajanje: int = field(default=0)
    placilo: float = field(default=0.0)
    podjetje: str = field(default="")   # join na podjetje
    podrocje: str = field(default="")   # join na področje
    stevilo_mest: int = field(default=0) 

# -----------------------------
@dataclass_json
@dataclass
class Prijava:
    id: int = field(default=0)
    status: str = field(default="") # npr. "v obravnavi", "odobrena", "zavrnjena"
    datum: datetime = field(default=datetime.now())
    student_emso: str = field(default="")     # referenca na Student
    pripravnistvo_id: int = field(default=0)  # referenca na Pripravnistvo


# -----------------------------
@dataclass_json
@dataclass
class Uporabnik:
    username: str = field(default="")
    role: str = field(default="")   # "student" ali "podjetje"
    password_hash: str = field(default="")
    last_login: str = field(default="")

@dataclass
class UporabnikDto:
    username: str = field(default="")
    role: str = field(default="")
    