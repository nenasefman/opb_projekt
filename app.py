from functools import wraps
from bottle import redirect, HTTPResponse, request, response, template, get, post, url
from Presentation.bottleext import *
from Services.pripravnistva_service import PripravnistvaService
from Services.auth_service import AuthService
from Data.models import Student, Podjetje
import os

service = PripravnistvaService()
auth = AuthService()

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

@route('/', method=['GET', 'POST'])
def index():
    uporabnik = request.get_cookie("uporabnik")
    if not uporabnik:
        redirect(url('prijava_get'))

    rola = request.get_cookie("rola")
    if rola == 'student':
        raise redirect(url('student_home'))
    elif rola == 'podjetje':
        raise redirect(url('podjetje_home'))
    elif rola == 'admin':
        redirect(url('admin'))
        return template('prijava.html', uporabnik=None, rola=None, napaka=None)

@get('/student/home', name='student_home')
@cookie_required
def student_home():
    '''Domača stran za študente, kjer vidijo seznam pripravništev'''        
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    
    if rola != 'student':
        raise redirect(url('index'))
    
    pripravnistva = service.dobi_vsa_pripravnistva_dto()
    
    return template('student_home.html', pripravnistva=pripravnistva, username=username, rola=rola, napaka=None)


@get('/podjetje/home', name='podjetje_home')
@cookie_required
def podjetje_home():
    '''Domača stran za podjetja, kjer vidijo prijave na svoja pripravništva'''

    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    
    if rola != 'podjetje':
        raise redirect(url('index'))
    
    prijave = service.dobi_prijave_podjetja_dto(username)
    
    return template('podjetje_home.html', prijave=prijave, username=username, napaka=None)
    
# ------------------------------- PRIJAVA IN ODJAVA ------------------------------

# -------------------------------- PRIJAVA --------------------------------
@post('/prijava')
def prijava():
    """
    Prijavi uporabnika v aplikacijo. Če je prijava uspešna, ustvari piškotke o uporabniku in njegovi roli.
    Drugače sporoči, da je prijava neuspešna.
    """
    username = request.forms.get('username')
    password = request.forms.get('password')

    if not auth.obstaja_uporabnik(username):
        return template("prijava.html", napaka="Uporabnik s tem imenom ne obstaja.")

    prijava = auth.prijavi_uporabnika(username, password)
    if prijava:
        response.set_cookie("uporabnik", username)
        response.set_cookie("rola", prijava.role)

        # Direktna preusmeritev na ustrezno domačo stran
        if prijava.role == 'admin':
            raise redirect(url('urejanje'))
        elif prijava.role == 'student':
            raise redirect(url('student_home'))
        elif prijava.role == 'podjetje':
            raise redirect(url('podjetje_home'))
        else:
            raise redirect(url('prijava_get'))
    else:
        return template("prijava.html", uporabnik=None, rola=None, napaka="Neuspešna prijava. Napačno geslo ali uporabniško ime.")

@get('/prijava', name='prijava_get')
def prijava_get():
    return template('prijava.html', uporabnik=None, rola=None, napaka=None)

# -------------------------------- ODJAVA --------------------------------
@get('/odjava', name='odjava')
def odjava():
    """
    Odjavi uporabnika iz aplikacije. Pobriše piškotke o uporabniku in njegovi roli.
    """
    response.delete_cookie("uporabnik")
    response.delete_cookie("rola")
    return template('prijava.html', uporabnik=None, rola=None, napaka=None)


# ------------------------------- REGISTRACIJA ------------------------------

# Prikaz obrazca za registracijo
@get('/registracija', name='registracija')
def registracija_get():
    return template('registracija.html', napaka=None, username="", role="student")

@post('/registracija')
def registracija_post():
    username = request.forms.get('username')
    password = request.forms.get('password')
    confirm_password = request.forms.get('confirm_password')
    role = request.forms.get('role')  # admin / student / podjetje

    # Validacija gesla
    if password != confirm_password:
        return template('registracija.html', napaka="Gesli se ne ujemata!", username = username, role=role)

    # Preverimo, ali uporabnik že obstaja
    if auth.obstaja_uporabnik(username):
        return template('registracija.html', napaka="Uporabnik s tem imenom že obstaja!", username = username, role=role)

    # Ustvarimo uporabnika v bazi (tabela uporabnik)
    try:
        auth.dodaj_uporabnika(username, role, password)
    except ValueError as ve:
        return template('registracija.html', napaka=str(ve))
    except Exception as e:
        return template('registracija.html', napaka=f"Napaka pri registraciji: {e}")


    # Shranimo username in role v piškotek, da ga uporabimo v naslednjem koraku
    response.set_cookie("reg_username", username)
    response.set_cookie("reg_role", role)

    # Preusmeritev na nadaljevanje registracije glede na vlogo
    if role == 'student':
        redirect(url('student_registracija'))
    elif role == 'podjetje':
        redirect(url('podjetje_registracija'))
    elif role == 'admin':
        redirect(url('admin_registracija'))  

# Prikaz obrazca za študenta
@get('/student_registracija', name='student_registracija')
def student_registracija_get():
    username = request.get_cookie("reg_username")
    role = request.get_cookie("reg_role")

    if not username or role != "student":
        redirect(url('registracija'))  # fallback na osnovno registracijo
    
    return template('student_registracija.html', napaka=None, username=None, 
                    ime="", priimek="", kontakt_tel="", povprecna_ocena="", univerza="")

@post('/student_registracija')
def student_registracija_post():
    # Preberemo username iz piškotka
    username = request.get_cookie("reg_username")
    role = request.get_cookie("reg_role")

    if not username or role != "student":
        redirect(url('registracija'))

    # Podatki iz obrazca
    ime = request.forms.get('ime')
    priimek = request.forms.get('priimek')
    kontakt_tel = request.forms.get('kontakt_tel')
    povprecna_ocena = request.forms.get('povprecna_ocena')
    univerza = request.forms.get('univerza')

    # Preverimo, če podjetje s tem username že obstaja
    if service.dobi_studenta(username):
        return template('student_registracija.html', napaka="Študent s tem uporabniškim imenom že obstaja!", 
                        username=username, ime=ime, priimek=priimek, kontakt_tel=kontakt_tel, 
                        povprecna_ocena=povprecna_ocena, univerza=univerza)

    # Ustvarimo nov objekt Študent in ga dodamo v bazo
    try:
        nov_student = Student(
            username=username,
            ime=ime,
            priimek=priimek,
            kontakt_tel=int(kontakt_tel),
            povprecna_ocena=float(povprecna_ocena),
            univerza=univerza
        )
        service.dodaj_studenta(nov_student)
    
    except HTTPResponse as r:   # to pusti redirectu da gre naprej
        raise r
    except Exception as e:
        import traceback
        traceback.print_exc()   # izpiše cel stacktrace v konzolo
        return template('student_registracija.html', napaka=f"Napaka pri registraciji: {e}", 
                        username=username, ime=ime, priimek=priimek, kontakt_tel=kontakt_tel, 
                        povprecna_ocena=povprecna_ocena, univerza=univerza)
    
    # Po uspešni registraciji pobrišemo piškotke in preusmerimo na prijavo
    response.delete_cookie("reg_username")
    response.delete_cookie("reg_role")
    return redirect(url('prijava_get'))


# Prikaz obrazca za podjetje
@get('/podjetje_registracija', name='podjetje_registracija')
def podjetje_registracija_get():
    # Preverimo, če imamo username in role v piškotku
    username = request.get_cookie("reg_username")
    role = request.get_cookie("reg_role")

    if not username or role != "podjetje":
        redirect(url('registracija'))  # fallback na osnovno registracijo

    return template('podjetje_registracija.html', napaka=None, username=None, ime="", kontakt_mail="", sedez="")


@post('/podjetje_registracija')
def podjetje_registracija_post():
    # Preberemo username iz piškotka
    username = request.get_cookie("reg_username")
    role = request.get_cookie("reg_role")

    if not username or role != "podjetje":
        redirect(url('registracija'))

    # Podatki iz obrazca
    ime = request.forms.get('ime')
    sedez = request.forms.get('sedez')
    kontakt_mail = request.forms.get('kontakt_mail')

    # Preverimo, če podjetje s tem username že obstaja
    if service.dobi_podjetje(username):
        return template('podjetje_registracija.html', napaka="Podjetje s tem uporabniškim imenom že obstaja!", 
                        username=username, ime=ime, kontakt_mail=kontakt_mail, sedez=sedez)

    # Ustvarimo nov objekt Podjetje in ga dodamo v bazo
    try:
        novo_podjetje = Podjetje(
            username=username,
            ime=ime,
            sedez=sedez,
            kontakt_mail=kontakt_mail
        )
        service.dodaj_podjetje(novo_podjetje)
    
    except HTTPResponse as r:   # to pusti redirectu da gre naprej
        raise r
    except Exception as e:
        import traceback
        traceback.print_exc()   # izpiše cel stacktrace v konzolo
        return template('podjetje_registracija.html', napaka=f"Napaka pri registraciji: {e}", 
                        username=username, ime=ime, kontakt_mail=kontakt_mail, sedez=sedez)
    
    # Po uspešni registraciji pobrišemo piškotke in preusmerimo na prijavo
    response.delete_cookie("reg_username")
    response.delete_cookie("reg_role")
    return redirect(url('prijava_get'))


# # ------------------------------- PROFIL ŠTUDENTA ------------------------------

@get('/student/profil', name='student_profil')
@cookie_required
def student_profil():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != "student":
        redirect(url('index'))
    # Pridobimo podatke o študentu
    student = service.dobi_studenta_dto(username)
    if not student:
        return template('napaka.html', napaka="Profil študenta ne obstaja.")
    return template('student_profil.html', student=student)

@get('/student/profil/uredi')
@cookie_required
def student_uredi_get():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != "student":
        redirect(url('index'))
    student = service.dobi_studenta(username)
    if not student:
        redirect(url('student_profil'))
    return template('student_uredi.html', student=student, napaka=None)

@post('/student/profil/uredi')
@cookie_required
def student_uredi_post():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != "student":
        redirect(url('index'))
    # Originalni podatki študenta
    student_og = service.dobi_studenta(username)
    # Podatki iz obrazca
    ime = request.forms.get('ime')
    priimek = request.forms.get('priimek')
    kontakt_tel = request.forms.get('kontakt_tel')
    povprecna_ocena = request.forms.get('povprecna_ocena')
    univerza = request.forms.get('univerza')
    try:
        # Posodobimo objekt
        student = Student(
            username=username,
            ime=ime,
            priimek=priimek,
            kontakt_tel=int(kontakt_tel) if kontakt_tel else student_og.kontakt_tel,
            povprecna_ocena=float(povprecna_ocena) if povprecna_ocena else student_og.povprecna_ocena,
            univerza=univerza if univerza else student_og.univerza
        )
        service.posodobi_studenta(student)
    except HTTPResponse as r:   # to pusti redirectu da gre naprej
        raise r
    except Exception as e:
        return template('student_uredi.html', student=student, napaka=f"Napaka: {e}")
    raise redirect(url('student_profil'))

# # ------------------------------- PROFIL PODJETJA ------------------------------

@get('/podjetje/profil', name='podjetje_profil')
@cookie_required
def podjetje_profil():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != "podjetje":
        redirect(url('index'))
    # Pridobimo podatke o podjetju
    podjetje = service.dobi_podjetje_dto(username)
    if not podjetje:
        return template('napaka.html', napaka="Profil podjetje ne obstaja.")
    return template('podjetje_profil.html', podjetje=podjetje)

@get('/podjetje/profil/uredi')
@cookie_required
def podjetje_uredi_get():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != "podjetje":
        redirect(url('index'))
    podjetje = service.dobi_podjetje(username)
    if not podjetje:
        redirect(url('podjetje_profil'))
    return template('podjetje_uredi.html', podjetje=podjetje, napaka=None)

@post('/podjetje/profil/uredi')
@cookie_required
def podjetje_uredi_post():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != "podjetje":
        redirect(url('index'))
    # Originalni podatki podjetja
    podjetje_og = service.dobi_podjetje(username)
    # Podatki iz obrazca
    ime = request.forms.get('ime')
    sedez = request.forms.get('sedez')
    kontakt_mail = request.forms.get('kontakt_mail')
    try:
        # Posodobimo objekt
        podjetje = Podjetje(
            username=username,
            ime=ime,
            sedez=sedez if sedez else podjetje_og.sedez,
            kontakt_mail=kontakt_mail if kontakt_mail else podjetje_og.kontakt_mail
        )
        service.posodobi_podjetje(podjetje)
    except HTTPResponse as r:   # to pusti redirectu da gre naprej
        raise r
    except Exception as e:
        return template('podjetje_uredi.html', podjetje=podjetje, napaka=f"Napaka: {e}")
    raise redirect(url('podjetje_profil'))

# ############################### PRIPRAVNIŠTVA ##############################

# #@get('/pripravnistva')
# #@cookie_required
# #def pripravnistva_list():
# #    rola = request.get_cookie("rola")
# #    pripravnistva_dto = service.dobi_vsa_pripravnistva_dto()
# #    return template('pripravnistva_list.html', pripravnistva=pripravnistva_dto, rola=rola)
# #
# #@get('/pripravnistvo/<id:int>')
# #@cookie_required
# #def pripravnistvo_detail(id):
# #    rola = request.get_cookie("rola")
# #    pripravnistvo = service.dobi_pripravnistvo_dto(id) # Uporabimo DTO za prikaz
# #    
# #    if pripravnistvo:
# #        return template('pripravnistvo_detail.html', pripravnistvo=pripravnistvo, rola=rola, napaka=None)
# #    else:
# #        return template('pripravnistvo_detail.html', pripravnistvo=None, rola=rola, napaka="Pripravništvo ni najdeno.")
# #
# #@get('/pripravnistvo/dodaj')
# #@cookie_required
# #def pripravnistvo_dodaj_get():
# #    rola = request.get_cookie("rola")
# #    if rola not in ['admin', 'podjetje']:
# #        redirect(url('index')) # Samo admin in podjetja lahko dodajajo
# #    
# #    podrocja_dto = service.dobi_vsa_podrocja_dto() # Predpostavimo metodo za pridobivanje področij
# #    return template('pripravnistvo_dodaj.html', podrocja=podrocja_dto, napaka=None)
# #
# #@post('/pripravnistvo/dodaj')
# #@cookie_required
# #def pripravnistvo_dodaj_post():
# #    username = request.get_cookie("uporabnik")
# #    rola = request.get_cookie("rola")
# #    if rola not in ['admin', 'podjetje']:
# #        redirect(url('index'))
# #    
# #    podjetje_list = service.dobi_podjetje(username)
# #    podjetje = podjetje_list[0] if podjetje_list else None
# #
# #    if not podjetje:
# #        podrocja_dto = service.dobi_vsa_podrocja_dto()
# #        return template('pripravnistvo_dodaj.html', podrocja=podrocja_dto, napaka="Podjetje ni najdeno. Napaka pri dodajanju pripravništva.")
# #
# #    try:
# #        new_pripravnistvo = Pripravnistvo(
# #            id=None,
# #            placilo=float(request.forms.get('placilo')),
# #            trajanje=request.forms.get('trajanje'),
# #            kraj=request.forms.get('kraj'),
# #            drzava=request.forms.get('drzava'),
# #            delovno_mesto=request.forms.get('delovno_mesto'),
# #            podjetje_id=podjetje.id,
# #            podrocje_id=int(request.forms.get('podrocje_id'))
# #        )
# #        service.dodaj_pripravnistvo(new_pripravnistvo)
# #        redirect(url('pripravnistva_list'))
# #    except Exception as e:
# #        podrocja_dto = service.dobi_vsa_podrocja_dto()
# #        return template('pripravnistvo_dodaj.html', podrocja=podrocja_dto, napaka=f"Napaka pri dodajanju pripravništva: {e}")
# #
# ## Urejanje pripravništva
# #@get('/pripravnistvo/uredi/<id:int>')
# #@cookie_required
# #def pripravnistvo_uredi_get(id):
# #    username = request.get_cookie("uporabnik")
# #    rola = request.get_cookie("rola")
# #    if rola not in ['admin', 'podjetje']:
# #        redirect(url('index'))
# #    
# #    pripravnistvo = service.dobi_pripravnistvo(id)
# #    if not pripravnistvo:
# #        redirect(url('pripravnistva_list'))
# #
# #    # Preverimo, ali je podjetje lastnik pripravništva (če ni admin)
# #    if rola == 'podjetje':
# #        podjetje_list = service.dobi_podjetje(username)
# #        podjetje = podjetje_list[0] if podjetje_list else None
# #        if not podjetje or pripravnistvo.podjetje_id != podjetje.id:
# #            redirect(url('index')) # Ni dovoljenja za urejanje
# #
# #    podrocja_dto = service.dobi_vsa_podrocja_dto()
# #    return template('pripravnistvo_uredi.html', pripravnistvo=pripravnistvo, podrocja=podrocja_dto, napaka=None)
# #
# #@post('/pripravnistvo/uredi/<id:int>')
# #@cookie_required
# #def pripravnistvo_uredi_post(id):
# #    username = request.get_cookie("uporabnik")
# #    rola = request.get_cookie("rola")
# #    if rola not in ['admin', 'podjetje']:
# #        redirect(url('index'))
# #
# #    pripravnistvo = service.dobi_pripravnistvo(id)
# #    if not pripravnistvo:
# #        redirect(url('pripravnistva_list'))
# #    
# #    if rola == 'podjetje':
# #        podjetje_list = service.dobi_podjetje(username)
# #        podjetje = podjetje_list[0] if podjetje_list else None
# #        if not podjetje or pripravnistvo.podjetje_id != podjetje.id:
# #            redirect(url('index'))
# #
# #    try:
# #        pripravnistvo.placilo = float(request.forms.get('placilo'))
# #        pripravnistvo.trajanje = request.forms.get('trajanje')
# #        pripravnistvo.kraj = request.forms.get('kraj')
# #        pripravnistvo.drzava = request.forms.get('drzava')
# #        pripravnistvo.delovno_mesto = request.forms.get('delovno_mesto')
# #        pripravnistvo.podrocje_id = int(request.forms.get('podrocje_id'))
# #        
# #        service.posodobi_pripravnistvo(pripravnistvo)
# #        redirect(url('pripravnistvo_detail', id=id))
# #    except Exception as e:
# #        podrocja_dto = service.dobi_vsa_podrocja_dto()
# #        return template('pripravnistvo_uredi.html', pripravnistvo=pripravnistvo, podrocja=podrocja_dto, napaka=f"Napaka pri posodabljanju: {e}")
# #
# #@get('/pripravnistvo/izbrisi/<id:int>')
# #@cookie_required
# #def pripravnistvo_izbrisi(id):
# #    rola = request.get_cookie("rola")
# #    if rola not in ['admin', 'podjetje']:
# #        redirect(url('index'))
# #    
# #    try:
# #        service.izbrisi_pripravnistvo(id)
# #        redirect(url('pripravnistva_list'))
# #    except Exception as e:
# #        # Lahko prikažete napako na strani s pripravništvi ali specifično obvestilo
# #        return "Napaka pri brisanju pripravništva."
# #
# #
# ---------------------------- PRIJAVE NA PRIPRAVNIŠTVA ---------------------------

@post('/pripravnistvo/<pripravnistvo_id:int>/prijava')
@cookie_required
def prijava_na_pripravnistvo(pripravnistvo_id):
   username = request.get_cookie("uporabnik")
   rola = request.get_cookie("rola")
   if rola != 'student':
       redirect(url('index'))

   student = service.dobi_studenta(username)

   if not student:
       return template('prijava_na_pripravnistvo.html', napaka="Študent ni najden. Prosimo, prijavite se ponovno.", rola=rola, pripravnistvo=service.dobi_pripravnistvo_dto(pripravnistvo_id))

   try:
       new_prijava = Prijava(
           id=None,
           status="V obravnavi", # Privzeti status
           datum=datetime.now().date(),
           student_emso=student.username,
           pripravnistvo_id=pripravnistvo_id
       )
       service.dodaj_prijavo(new_prijava) # Predpostavimo metodo za dodajanje prijave
       redirect(url('student_profil')) # Preusmerimo na profil študenta, da vidi prijave
   except Exception as e:
       return template('prijava_na_pripravnistvo.html', napaka=f"Napaka pri prijavi: {e}", rola=rola, pripravnistvo=service.dobi_pripravnistvo_dto(pripravnistvo_id))


# @get('/podjetje/prijave')
# @cookie_required
# def podjetje_prijave():
#    username = request.get_cookie("uporabnik")
#    rola = request.get_cookie("rola")
#    if rola != 'podjetje':
#        redirect(url('index'))
   
#    podjetje_list = service.dobi_podjetje(username)
#    podjetje = podjetje_list[0] if podjetje_list else None
   
#    if not podjetje:
#        redirect(url('index'))

#    prijave_dto = service.dobi_prijave_podjetja_dto(username) # Uporabimo username, ker je podjetje identificirano z njim
#    return template('podjetje_prijave.html', prijave=prijave_dto, rola=rola)

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

# ------------------------------- VSE PRIJAVE ŠTUDENTA ------------------------------

@get('/student/prijave', name='student_prijave')
@cookie_required
def student_prijave():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    
    # Dovoli dostop samo študentom
    if rola != 'student':
        redirect(url('index'))
    
    # Poiščemo podatke o študentu
    student = service.dobi_studenta(username)
    
    if not student:
        redirect(url('index'))

    # Pridobimo seznam pripravništev, na katera je prijavljen
    prijave = service.dobi_prijave_studenta_dto(student.username)  
    # Ta metoda mora vrniti seznam prijav z vsemi podatki o pripravništvih.

    return template('moje_prijave.html', prijave=prijave, username=username, rola=rola, napaka=None)


# ############################### ADMINISTRATOR ##############################
# #
# #@get('/admin')
# #@cookie_required
# #def urejanje_admin_panel():
# #    username = request.get_cookie("uporabnik")
# #    rola = request.get_cookie("rola")
# #    
# #    if rola != 'admin':
# #        redirect(url('index'))
# #    
# #    # Tukaj lahko prikažemo splošen admin panel z različnimi možnostmi
# #    # npr. urejanje uporabnikov, pregled vseh podatkov, statistika itd.
# #    return template('admin_panel.html', rola=rola)
# #
# #
# Zaženemo strežnik 
if __name__ == '__main__':
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER, debug=True)