from functools import wraps
from bottle import redirect, HTTPResponse, request, response, template, get, post, url
from Presentation.bottleext import *
from Services.pripravnistva_service import PripravnistvaService
from Services.auth_service import AuthService
from Data.models import Student, Podjetje, Prijava, Pripravnistvo
import os
import traceback

service = PripravnistvaService()
auth = AuthService()

SERVER_PORT = int(os.environ.get('BOTTLE_PORT', 8080))
RELOADER = os.environ.get('BOTTLE_RELOADER', True)

# Odpravljaneje težav z encodingom
def fix_form_encoding(form):
    """Popravi vse vrednosti v obrazcu, da so UTF-8."""
    fixed = {}
    for key, value in form.items():
        if isinstance(value, str):
            # Pretvorba iz latin1 -> UTF-8
            fixed[key] = value.encode('latin1').decode('utf-8')
        else:
            fixed[key] = value
    return fixed

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
        raise redirect(url('prijava_get'))

    rola = request.get_cookie("rola")
    if rola == 'student':
        raise redirect(url('student_home'))
    elif rola == 'podjetje':
        redirect(url('podjetje_home'))
        return template('prijava.html', uporabnik=None, rola=None, napaka=None)
    

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
# ------------------------------- Osnovna registracija ------------------------------

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

# ------------------------------- Registracija študenta ------------------------------

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
    form = fix_form_encoding(request.forms)
    ime = form.get('ime')
    priimek = form.get('priimek')
    kontakt_tel = form.get('kontakt_tel')
    povprecna_ocena = form.get('povprecna_ocena')
    univerza = form.get('univerza')

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
            kontakt_tel=kontakt_tel,
            povprecna_ocena=float(povprecna_ocena),
            univerza=univerza
        )
        service.dodaj_studenta(nov_student)
    
    except HTTPResponse as r:   # to pusti redirectu da gre naprej
        raise r
    except Exception as e:
        traceback.print_exc()   # izpiše cel stacktrace v konzolo
        return template('student_registracija.html', napaka=f"Napaka pri registraciji: {e}", 
                        username=username, ime=ime, priimek=priimek, kontakt_tel=kontakt_tel, 
                        povprecna_ocena=povprecna_ocena, univerza=univerza)
    
    # Po uspešni registraciji pobrišemo piškotke in preusmerimo na prijavo
    response.delete_cookie("reg_username")
    response.delete_cookie("reg_role")
    return redirect(url('prijava_get'))

# ------------------------------- Registracija podjetja ------------------------------

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
    form = fix_form_encoding(request.forms)
    ime = form.get('ime')
    sedez = form.get('sedez')
    kontakt_mail = form.get('kontakt_mail')

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
        traceback.print_exc()   # izpiše cel stacktrace v konzolo
        return template('podjetje_registracija.html', napaka=f"Napaka pri registraciji: {e}", 
                        username=username, ime=ime, kontakt_mail=kontakt_mail, sedez=sedez)
    
    # Po uspešni registraciji pobrišemo piškotke in preusmerimo na prijavo
    response.delete_cookie("reg_username")
    response.delete_cookie("reg_role")
    return redirect(url('prijava_get'))



# ------------------------------- ZA ŠTUDENTE ------------------------------

# ------------------------------- DOMAČA STRAN ŠTUDENTA ------------------------------

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


# ------------------------------- PROFIL ŠTUDENTA ------------------------------

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


@get('/student/<username>', name='student_profil_za_podjetja')
def student_profil_za_podjetja(username):
    """
    Prikaže profil določenega študenta na podlagi njegovega uporabniškega imena.
    """
    # Tukaj dobiš podatke o študentu iz baze
    student = service.dobi_studenta(student.ime)
    if not student:
        return template("napaka.html", sporocilo="Študent ne obstaja.", napaka=None)
    return template("profil_studenta_za_podjetje.html", student=student, napaka=None)


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
    form = fix_form_encoding(request.forms)

    ime = form.get('ime')
    priimek = form.get('priimek')
    kontakt_tel = form.get('kontakt_tel')
    povprecna_ocena = form.get('povprecna_ocena')
    univerza = form.get('univerza')
    try:
        # Posodobimo objekt
        student = Student(
            username=username,
            ime=ime,
            priimek=priimek,
            kontakt_tel=kontakt_tel if kontakt_tel else student_og.kontakt_tel,
            povprecna_ocena=float(povprecna_ocena) if povprecna_ocena else student_og.povprecna_ocena,
            univerza=univerza if univerza else student_og.univerza
        )
        service.posodobi_studenta(student)
    except HTTPResponse as r:   # to pusti redirectu da gre naprej
        raise r
    except Exception as e:
        return template('student_uredi.html', student=student, napaka=f"Napaka: {e}")
    raise redirect(url('student_profil'))

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


# ---------------------------- PRIJAVE NA PRIPRAVNIŠTVA ---------------------------

@get('/pripravnistvo/<id:int>/prijava')
@cookie_required
def prijava_na_pripravnistvo_get(id):
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")

    if rola != "student":
        return redirect(url('index'))

    pripravnistvo = service.dobi_pripravnistvo(id)

    return template(
        'prijava_na_pripravnistvo.html',
        napaka=None,
        rola=rola,
        pripravnistvo=pripravnistvo,
        student=username
    )


@post('/pripravnistvo/<pripravnistvo_id:int>/prijava')
@cookie_required
def prijava_na_pripravnistvo_post(pripravnistvo_id):
   username = request.get_cookie("uporabnik")
   rola = request.get_cookie("rola")
   if rola != 'student':
       redirect(url('index'))

   try:
        # preveri, ali je že prijavljen na to pripravništvo
        obstojece = service.dobi_prijavo_studenta(username, pripravnistvo_id)
        if obstojece:
            return template(
                'prijava_na_pripravnistvo.html',
                napaka="Na to pripravništvo si se že prijavil!",
                rola=rola,
                pripravnistvo=service.dobi_pripravnistvo(pripravnistvo_id),
                student=username
            )

        # ustvari prijavo
        prijava = Prijava(
            id=None,
            status="v obravnavi",
            datum_prijave=datetime.now(),
            student=username,
            pripravnistvo=pripravnistvo_id
        )
        service.dodaj_prijavo(prijava)
   except Exception as e:
        print(traceback.format_exc())
        return template(
            'prijava_na_pripravnistvo.html',
            napaka=f"Napaka pri oddaji prijave: {str(e)}",
            rola=rola,
            pripravnistvo=service.dobi_pripravnistvo(pripravnistvo_id),
            student=username
        )

   return redirect(url('student_home'))

# ------------------------------- PRIPRAVNIŠTVA PODROBNOSTI ------------------------------

@get('/pripravnistvo/<id:int>', name='pripravnistvo_podrobnosti')
@cookie_required
def pripravnistvo_podrobnosti(id):
    pripravnistvo = service.dobi_pripravnistvo(id) 

    if not pripravnistvo:
        return template('napaka.html', sporocilo="Pripravništvo ne obstaja.")
    
    podjetje = service.dobi_podjetje(pripravnistvo.podjetje)
    
    return template('pripravnistvo_podrobnosti.html',
                    pripravnistvo=pripravnistvo,
                    podjetje=podjetje,
                    rola=request.get_cookie("rola"))












# ------------------------------- ZA PODJETJA ------------------------------

# ------------------------------- DOMAČA STRAN PODJETJA ------------------------------

@get('/podjetje/home', name='podjetje_home')
@cookie_required
def podjetje_home():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    
    if rola != 'podjetje':
        raise redirect(url('index'))
    
    podjetje = service.dobi_podjetje_dto(username)
    if not podjetje:
        return template('napaka.html', napaka="Profil podjetja ne obstaja.")

    vsa_pripravnistva = service.dobi_vsa_pripravnistva_dto()
    # preveri, da je p.podjetje == podjetje.username ali podjetje.ime
    pripravnistva = [p for p in vsa_pripravnistva if p.podjetje == podjetje.ime]
    
    prijave = service.dobi_prijave_podjetja_dto(username)
    
    return template('podjetje_home.html', prijave=prijave, pripravnistva=pripravnistva, podjetje=podjetje, username=username, napaka=None)

# ------------------------------- PROFIL PODJETJA ------------------------------

@get('/podjetje/profil', name='podjetje_profil')
@cookie_required
def podjetje_profil():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")

    if rola != "podjetje":
        redirect(url('index'))

    podjetje = service.dobi_podjetje_dto(username)
    if not podjetje:
        return template('napaka.html', napaka="Profil podjetja ne obstaja.")

    if rola != "podjetje":
        return template('napaka.html', napaka="Profil podjetje ne obstaja.")
    return template('podjetje_profil.html', podjetje=podjetje, username=username, napaka=None)


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
    form = fix_form_encoding(request.forms)
    ime = form.get('ime')
    sedez = form.get('sedez')
    kontakt_mail = form.get('kontakt_mail')
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


# ------------------------------- DODAJ NOVO PRIPRAVNIŠTVO ------------------------------

@get('/pripravnistvo/dodaj', name='pripravnistvo_dodaj_get')
@cookie_required
def pripravnistvo_dodaj_get():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")

    if rola != "podjetje":
        redirect(url('index'))  # Samo podjetja lahko dodajajo

    podjetje = service.dobi_podjetje(username)

    return template('novo_pripravnistvo.html', napaka=None, podjetje=podjetje)


@post('/pripravnistvo/dodaj', name='pripravnistvo_dodaj_post')
@cookie_required
def pripravnistvo_dodaj_post():
    username = request.get_cookie("uporabnik")
    rola = request.get_cookie("rola")
    if rola != "podjetje":
        redirect(url('index'))

    podjetje = service.dobi_podjetje(username)
    if not podjetje:
        return template('novo_pripravnistvo.html', napaka="Podjetje ni najdeno. Napaka pri dodajanju pripravništva.")

    try:
        form = fix_form_encoding(request.forms)
        novo_pripravnistvo = Pripravnistvo(
            id=None,
            podjetje=podjetje.username,
            placilo=float(form.get('placilo')),
            trajanje=form.get('trajanje'),
            kraj=form.get('kraj'),
            drzava=form.get('drzava'),
            delovno_mesto=form.get('delovno_mesto'),
            opis_dela=form.get('opis_dela'),
            stevilo_mest=form.get('stevilo_mest')
        )
        service.dodaj_pripravnistvo(novo_pripravnistvo)

        # Namesto redirecta vrnemo nov HTML template
        return template('oddaja_uspesna.html', podjetje=podjetje, rola=rola) 
    except Exception as e:
        return template('novo_pripravnistvo.html', napaka=f"Napaka pri dodajanju pripravništva: {e}")
    

# ------------------------------- UREJANJE PRIPRAVNIŠTVA ------------------------------

@get('/pripravnistvo/uredi/<id:int>')
@cookie_required
def pripravnistvo_uredi_get(id):
    rola = request.get_cookie("rola")

    if rola != 'podjetje':
        redirect(url('index'))

    pripravnistvo = service.dobi_pripravnistvo(id)
    if not pripravnistvo:
        redirect(url('podjetje_home'))

    return template(
        'pripravnistvo_uredi.html',
        pripravnistvo=pripravnistvo,
        napaka=None
    )

@post('/pripravnistvo/uredi/<id:int>')
@cookie_required
def pripravnistvo_uredi_post(id):
    rola = request.get_cookie("rola")

    if rola != 'podjetje':
        redirect(url('index'))

    pripravnistvo = service.dobi_pripravnistvo(id)

    try:
        form = fix_form_encoding(request.forms)
        pripravnistvo.placilo = float(form.get('placilo'))
        pripravnistvo.trajanje = int(form.get('trajanje'))
        pripravnistvo.kraj = form.get('kraj')
        pripravnistvo.drzava = form.get('drzava')
        pripravnistvo.delovno_mesto = form.get('delovno_mesto')
        pripravnistvo.opis_dela = form.get('opis_dela')
        pripravnistvo.stevilo_mest = int(form.get('stevilo_mest'))

        service.posodobi_pripravnistvo(pripravnistvo)

    except Exception as e:
        return template(
            'pripravnistvo_uredi.html',
            pripravnistvo=pripravnistvo,
            napaka=f"Napaka pri posodabljanju: {e}"
        )
    
    redirect(url('podjetje_home'))

# ------------------------------- OGLED PRIJAV NA PRIPRAVNIŠTVO ------------------------------

@get('/pripravnistvo/prijave/<id:int>')
@cookie_required
def pripravnistvo_prijave(id):
    rola = request.get_cookie("rola")

    if rola != 'podjetje':
        redirect(url('index'))

    pripravnistvo = service.dobi_pripravnistvo(id)
    if not pripravnistvo:
        redirect(url('podjetje_home'))

    prijave = service.dobi_prijave_na_pripravnistvo(id)

    # Za vsako prijavo dobim še podatko o študentu
    prijave_s_podatki = []
    for prijava in prijave:
        student = service.dobi_studenta(prijava.student)
        prijave_s_podatki.append({
            'prijava': prijava,
            'student': student})

    return template(
        'prijave_na_pripravnistvo.html',
        pripravnistvo=pripravnistvo,
        prijave=prijave_s_podatki
    )

@post('/prijava/posodobi_status/<id_prijave>', name='prijava_posodobi_status')
@cookie_required
def prijava_posodobi_status(id_prijave):
    ''' Posodobi status prijave '''
    nov_status = request.forms.get('nov_status')
    prijava_id = int(id_prijave)
    
    if not nov_status:
        # Če status ni poslan, se vrnemo nazaj z napako
        referer = request.headers.get('Referer')
        if referer:
            return template("napaka.html", napaka="Napaka: Status ni bil izbran.")
        else:
            redirect(url('podjetje_home'))

    service.posodobi_status_prijave(prijava_id, nov_status)
    
    # Preusmerimo nazaj na isto stran
    referer = request.headers.get('Referer')
    if referer:
        redirect(referer)
    else:
        # Če referer ni na voljo, preusmerimo na domačo stran podjetja
        redirect(url('podjetje_home'))


# ------------------------------- POGANJANJE APPA ------------------------------

if __name__ == '__main__':
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER, debug=True)