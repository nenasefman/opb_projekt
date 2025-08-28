from functools import wraps
from Presentation.bottleext import *
from Services.pripravnistva_service import PripravnistvaService
from Services.auth_service import AuthService
import os

# Ustvarimo instance servisov, ki jih potrebujemo.
service = PripravnistvaService()
auth = AuthService()

# privzete nastavitve
SERVER_PORT = int(os.environ.get('BOTTLE_PORT', 8080))
RELOADER = os.environ.get('BOTTLE_RELOADER', True)


def cookie_required(f):
    """
    Dekorator, ki zahteva veljaven piškotek. Če piškotka ni, uporabnika preusmeri na stran za prijavo.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        cookie = request.get_cookie("uporabnik")
        if cookie:
            return f(*args, **kwargs)
        return template("prijava.html", uporabnik=None, rola=None, napaka="Potrebna je prijava!")
    return decorated


@get('/')
@cookie_required
def index():
    username = request.get_cookie("uporabnik")
    role = request.get_cookie("rola")

    if role == 'admin':
        redirect(url('urejanje'))
    else:
        filter_text = request.query.filter_text or ''
        osebe_dto = service.dobi_(username)
        oseba = service.dobi_osebo(username)
        return template('domaca_stran.html', oseba=oseba, osebe=osebe_dto, filter_text=filter_text)
    
############################## PRIJAVA IN ODJAVA ##############################

@post('/prijava')
def prijava():
    """
    Prijavi uporabnika v aplikacijo. Če je prijava uspešna, ustvari piškotke o uporabniku in njegovi roli.
    Drugače sporoči, da je prijava neuspešna.
    """
    username = request.forms.get('username')
    password = request.forms.get('password')

    if not auth.obstaja_uporabnik(username):
        return template("prijava.html", napaka="Uporabnik s tem imenom ne obstaja")

    prijava = auth.prijavi_uporabnika(username, password)
    if prijava:
        response.set_cookie("uporabnik", username)
        response.set_cookie("rola", prijava.role)
        
        if prijava.role == 'admin':
            redirect(url('urejanje'))
        else:
            redirect(url('index'))
        
    else:
        return template("prijava.html", uporabnik=None, rola=None, napaka="Neuspešna prijava. Napačno geslo ali uporabniško ime.")

@get('/odjava')
def odjava():
    """
    Odjavi uporabnika iz aplikacije. Pobriše piškotke o uporabniku in njegovi roli.
    """
    response.delete_cookie("uporabnik")
    response.delete_cookie("rola")
    return template('prijava.html', uporabnik=None, rola=None, napaka=None)

################################### REGISTRACIJA ###################################

# izberemo vlogo; admin ali student ali podjetje
@app.get('/izbira_role')
def izbira_role():
    return template('izbira_role.html')

# glede na izbrano vlogo preusmeri na ustrezno registracijo
@app.post('/izbira_role')
def izbira_role_post():
    role = request.forms.get('role')
    if role == 'admin':
        # Preusmeri na admin registracijo
        redirect(url('admin_auth'))
    elif role == 'student':
        # Preusmeri na registracijo študenta
        redirect(url('student_registracija'))
    elif role == 'podjetje':
        # Preusmeri na registracijo podjetja
        redirect(url('register_podjetje'))




# Registracija študenta
@get('/student_registracija')
def student_registracija_get():
    return template('student_registracija.html', napaka=None)

@post('/student_registracija')
def student_registracija_post():
    # Podatki iz obrazca
    username = request.forms.get('username')
    password = request.forms.get('password')
    confirm_password = request.forms.get('confirm_password')
    ime = request.forms.get('ime')
    priimek = request.forms.get('priimek')
    kontakt = request.forms.get('kontakt')
    
    # Preverimo, ali uporabnik že obstaja
    if auth.obstaja_uporabnik(username):
        return template('student_registracija.html', napaka="Uporabnik s tem imenom že obstaja!")
    if service.dobi_studenta(username): # Preveri, če je študent z istim uporabniškim imenom že registriran
         return template('student_registracija.html', napaka="Študent s tem uporabniškim imenom že obstaja!")

    # Ustvarimo novega uporabnika in študenta
    try:
        auth.registriraj_uporabnika(username, password, 'student') # Registriraj v tabelo uporabnik
        new_student = Student(
            emso=emso,
            ime=ime,
            priimek=priimek,
            mail=mail,
            kontakt=kontakt,
            # povprecna_ocena in univerza_id bi lahko bili None ali privzete vrednosti ob registraciji
            povprecna_ocena=None,
            univerza_id=None, 
            username=username
        )
        service.dodaj_studenta(new_student)
        redirect(url('prijava_get')) # Po uspešni registraciji preusmerimo na prijavo
    except Exception as e:
        # Boljše obvladovanje napak
        return template('student_registracija.html', napaka=f"Napaka pri registraciji: {e}")




# Registracija podjetja
@get('/podjetje_registracija')
def podjetje_registracija_get():
    return template('podjetje_registracija.html', napaka=None)

@post('/podjetje_registracija')
def podjetje_registracija_post():
    username = request.forms.get('username')
    password = request.forms.get('password')
    ime_podjetja = request.forms.get('ime_podjetja')
    mail = request.forms.get('mail')
    sedez = request.forms.get('sedez')

    if auth.obstaja_uporabnik(username):
        return template('podjetje_registracija.html', napaka="Uporabnik s tem imenom že obstaja!")
    if service.dobi_podjetje(username):
        return template('podjetje_registracija.html', napaka="Podjetje s tem uporabniškim imenom že obstaja!")
    
    try:
        auth.registriraj_uporabnika(username, password, 'podjetje')
        new_podjetje = Podjetje(
            id=None, # ID se generira avtomatsko
            ime=ime_podjetja,
            mail=mail,
            sedez=sedez,
            kontakt=None, # Dodaj, če je potrebno
            username=username
        )
        service.dodaj_podjetje(new_podjetje)
        redirect(url('prijava_get'))
    except Exception as e:
        return template('podjetje_registracija.html', napaka=f"Napaka pri registraciji podjetja: {e}")








# Registracija/prijava admina (lahko je posebna pot ali preko obstoječe prijava_post z rolo)
@get('/admin_register')
def admin_register_get():
    return template('admin_register.html', napaka=None)

@post('/admin_register')
def admin_register_post():
    username = request.forms.get('username')
    password = request.forms.get('password')
    # Admin registracijo bi morali zaščititi, npr. z admin geslom ali samo preko baze
    
    if auth.obstaja_uporabnik(username):
        return template('admin_register.html', napaka="Admin uporabnik s tem imenom že obstaja!")
    
    try:
        auth.registriraj_uporabnika(username, password, 'admin')
        redirect(url('prijava_get'))
    except Exception as e:
        return template('admin_register.html', napaka=f"Napaka pri registraciji administratorja: {e}")


############################## ŠTUDENTI ##############################

@get('/student/profil')
@cookie_required
def student_profil():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    
    if rola != 'student':
        redirect(url('index')) # Samo študenti lahko dostopajo do svojega profila
    
    student_list = service.dobi_studenta(username)
    student = student_list[0] if student_list else None

    if student:
        prijave_dto = service.dobi_prijave_studenta_dto(username)
        return template('student_profil.html', student=student, prijave=prijave_dto, rola=rola, napaka=None)
    else:
        return template('student_profil.html', student=None, prijave=[], rola=rola, napaka="Študent ni najden.")

@get('/student/uredi')
@cookie_required
def student_uredi_get():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != 'student':
        redirect(url('index'))
    
    student_list = service.dobi_studenta(username)
    student = student_list[0] if student_list else None

    if student:
        return template('student_uredi.html', student=student, napaka=None)
    else:
        redirect(url('student_profil')) # Preusmeri nazaj, če študenta ni

@post('/student/uredi')
@cookie_required
def student_uredi_post():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != 'student':
        redirect(url('index'))

    student_list = service.dobi_studenta(username)
    student = student_list[0] if student_list else None

    if student:
        # Posodobimo podatke iz obrazca
        student.ime = request.forms.get('ime')
        student.priimek = request.forms.get('priimek')
        student.mail = request.forms.get('mail')
        student.kontakt = request.forms.get('kontakt')
        # povprecna_ocena in univerza_id se verjetno ne urejata direktno preko profila

        try:
            service.posodobi_studenta(student)
            redirect(url('student_profil'))
        except Exception as e:
            return template('student_uredi.html', student=student, napaka=f"Napaka pri posodabljanju: {e}")
    else:
        redirect(url('student_profil'))


############################## PODJETJA ##############################

@get('/podjetja')
@cookie_required
def podjetja_list():
    rola = request.get_cookie("rola")
    podjetja_dto = service.dobi_vsa_podjetja_dto()
    return template('podjetja_list.html', podjetja=podjetja_dto, rola=rola)

@get('/podjetje/<id:int>')
@cookie_required
def podjetje_profil(id):
    rola = request.get_cookie("rola")
    podjetje_list = service.dobi_podjetje_by_id(id) # Predpostavimo metodo, ki dobi podjetje po ID-ju
    podjetje = podjetje_list[0] if podjetje_list else None

    if podjetje:
        pripravnistva_dto = service.dobi_pripravnistva_podjetja_dto(id) # Predpostavimo metodo v service
        return template('podjetje_profil.html', podjetje=podjetje, pripravnistva=pripravnistva_dto, rola=rola, napaka=None)
    else:
        return template('podjetje_profil.html', podjetje=None, pripravnistva=[], rola=rola, napaka="Podjetje ni najdeno.")


############################## PRIPRAVNIŠTVA ##############################

@get('/pripravnistva')
@cookie_required
def pripravnistva_list():
    rola = request.get_cookie("rola")
    pripravnistva_dto = service.dobi_vsa_pripravnistva_dto()
    return template('pripravnistva_list.html', pripravnistva=pripravnistva_dto, rola=rola)

@get('/pripravnistvo/<id:int>')
@cookie_required
def pripravnistvo_detail(id):
    rola = request.get_cookie("rola")
    pripravnistvo = service.dobi_pripravnistvo_dto(id) # Uporabimo DTO za prikaz
    
    if pripravnistvo:
        return template('pripravnistvo_detail.html', pripravnistvo=pripravnistvo, rola=rola, napaka=None)
    else:
        return template('pripravnistvo_detail.html', pripravnistvo=None, rola=rola, napaka="Pripravništvo ni najdeno.")

@get('/pripravnistvo/dodaj')
@cookie_required
def pripravnistvo_dodaj_get():
    rola = request.get_cookie("rola")
    if rola not in ['admin', 'podjetje']:
        redirect(url('index')) # Samo admin in podjetja lahko dodajajo
    
    podrocja_dto = service.dobi_vsa_podrocja_dto() # Predpostavimo metodo za pridobivanje področij
    return template('pripravnistvo_dodaj.html', podrocja=podrocja_dto, napaka=None)

@post('/pripravnistvo/dodaj')
@cookie_required
def pripravnistvo_dodaj_post():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola not in ['admin', 'podjetje']:
        redirect(url('index'))
    
    podjetje_list = service.dobi_podjetje(username)
    podjetje = podjetje_list[0] if podjetje_list else None

    if not podjetje:
        podrocja_dto = service.dobi_vsa_podrocja_dto()
        return template('pripravnistvo_dodaj.html', podrocja=podrocja_dto, napaka="Podjetje ni najdeno. Napaka pri dodajanju pripravništva.")

    try:
        new_pripravnistvo = Pripravnistvo(
            id=None,
            placilo=float(request.forms.get('placilo')),
            trajanje=request.forms.get('trajanje'),
            kraj=request.forms.get('kraj'),
            drzava=request.forms.get('drzava'),
            delovno_mesto=request.forms.get('delovno_mesto'),
            podjetje_id=podjetje.id,
            podrocje_id=int(request.forms.get('podrocje_id'))
        )
        service.dodaj_pripravnistvo(new_pripravnistvo)
        redirect(url('pripravnistva_list'))
    except Exception as e:
        podrocja_dto = service.dobi_vsa_podrocja_dto()
        return template('pripravnistvo_dodaj.html', podrocja=podrocja_dto, napaka=f"Napaka pri dodajanju pripravništva: {e}")

# Urejanje pripravništva
@get('/pripravnistvo/uredi/<id:int>')
@cookie_required
def pripravnistvo_uredi_get(id):
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola not in ['admin', 'podjetje']:
        redirect(url('index'))
    
    pripravnistvo = service.dobi_pripravnistvo(id)
    if not pripravnistvo:
        redirect(url('pripravnistva_list'))

    # Preverimo, ali je podjetje lastnik pripravništva (če ni admin)
    if rola == 'podjetje':
        podjetje_list = service.dobi_podjetje(username)
        podjetje = podjetje_list[0] if podjetje_list else None
        if not podjetje or pripravnistvo.podjetje_id != podjetje.id:
            redirect(url('index')) # Ni dovoljenja za urejanje

    podrocja_dto = service.dobi_vsa_podrocja_dto()
    return template('pripravnistvo_uredi.html', pripravnistvo=pripravnistvo, podrocja=podrocja_dto, napaka=None)

@post('/pripravnistvo/uredi/<id:int>')
@cookie_required
def pripravnistvo_uredi_post(id):
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola not in ['admin', 'podjetje']:
        redirect(url('index'))

    pripravnistvo = service.dobi_pripravnistvo(id)
    if not pripravnistvo:
        redirect(url('pripravnistva_list'))
    
    if rola == 'podjetje':
        podjetje_list = service.dobi_podjetje(username)
        podjetje = podjetje_list[0] if podjetje_list else None
        if not podjetje or pripravnistvo.podjetje_id != podjetje.id:
            redirect(url('index'))

    try:
        pripravnistvo.placilo = float(request.forms.get('placilo'))
        pripravnistvo.trajanje = request.forms.get('trajanje')
        pripravnistvo.kraj = request.forms.get('kraj')
        pripravnistvo.drzava = request.forms.get('drzava')
        pripravnistvo.delovno_mesto = request.forms.get('delovno_mesto')
        pripravnistvo.podrocje_id = int(request.forms.get('podrocje_id'))
        
        service.posodobi_pripravnistvo(pripravnistvo)
        redirect(url('pripravnistvo_detail', id=id))
    except Exception as e:
        podrocja_dto = service.dobi_vsa_podrocja_dto()
        return template('pripravnistvo_uredi.html', pripravnistvo=pripravnistvo, podrocja=podrocja_dto, napaka=f"Napaka pri posodabljanju: {e}")

@get('/pripravnistvo/izbrisi/<id:int>')
@cookie_required
def pripravnistvo_izbrisi(id):
    rola = request.get_cookie("rola")
    if rola not in ['admin', 'podjetje']:
        redirect(url('index'))
    
    try:
        service.izbrisi_pripravnistvo(id)
        redirect(url('pripravnistva_list'))
    except Exception as e:
        # Lahko prikažete napako na strani s pripravništvi ali specifično obvestilo
        return "Napaka pri brisanju pripravništva."


############################## PRIJAVE ##############################

@post('/pripravnistvo/<pripravnistvo_id:int>/prijava')
@cookie_required
def prijava_na_pripravnistvo(pripravnistvo_id):
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != 'student':
        redirect(url('index'))

    student_list = service.dobi_studenta(username)
    student = student_list[0] if student_list else None

    if not student:
        return template('pripravnistvo_detail.html', napaka="Študent ni najden. Prosimo, prijavite se ponovno.", rola=rola, pripravnistvo=service.dobi_pripravnistvo_dto(pripravnistvo_id))

    try:
        new_prijava = Prijava(
            id=None,
            status="V obravnavi", # Privzeti status
            datum=datetime.now().date(),
            student_emso=student.emso,
            pripravnistvo_id=pripravnistvo_id
        )
        service.dodaj_prijavo(new_prijava) # Predpostavimo metodo za dodajanje prijave
        redirect(url('student_profil')) # Preusmerimo na profil študenta, da vidi prijave
    except Exception as e:
        return template('pripravnistvo_detail.html', napaka=f"Napaka pri prijavi: {e}", rola=rola, pripravnistvo=service.dobi_pripravnistvo_dto(pripravnistvo_id))


@get('/podjetje/prijave')
@cookie_required
def podjetje_prijave():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != 'podjetje':
        redirect(url('index'))
    
    podjetje_list = service.dobi_podjetje(username)
    podjetje = podjetje_list[0] if podjetje_list else None
    
    if not podjetje:
        redirect(url('index'))

    prijave_dto = service.dobi_prijave_podjetja_dto(username) # Uporabimo username, ker je podjetje identificirano z njim
    return template('podjetje_prijave.html', prijave=prijave_dto, rola=rola)

@post('/prijava/posodobi/<id:int>')
@cookie_required
def prijava_posodobi_status(id):
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != 'podjetje':
        redirect(url('index'))
    
    status = request.forms.get('status')
    prijava = service.dobi_prijavo_by_id(id) # Predpostavimo metodo, ki dobi prijavo po ID-ju
    
    if prijava:
        prijava.status = status
        service.posodobi_prijavo(prijava)
    
    redirect(url('podjetje_prijave')) # Preusmerimo nazaj na seznam prijav


############################## ADMINISTRATOR ##############################

@get('/admin')
@cookie_required
def urejanje_admin_panel():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    
    if rola != 'admin':
        redirect(url('index'))
    
    # Tukaj lahko prikažemo splošen admin panel z različnimi možnostmi
    # npr. urejanje uporabnikov, pregled vseh podatkov, statistika itd.
    return template('admin_panel.html', rola=rola)


# Zaženemo strežnik 
if __name__ == '__main__':
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER, debug=True)

