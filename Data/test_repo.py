from repository import Repo
from models import *


# V tej datoteki lahko testiramo funkcionalnost repozitorija,
# brez da zaganjamo celoten projekt.


repo = Repo()

# Dobimo vse osebe

student = repo.dobi_studenta('student1') # prvi element seznama
prijave = repo.dobi_prijave_studenta(student.username)
for prijava in prijave:
    print(prijava)