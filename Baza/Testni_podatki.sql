INSERT INTO Uporabnik (username, role, password_hash, last_login)
VALUES
    ('admin1', 'admin', 'hash_admin', NOW()),
    ('podjetje1', 'podjetje', 'hash_podjetje1', NOW() - INTERVAL '2 days'),
    ('podjetje2', 'podjetje', 'hash_podjetje2', NOW() - INTERVAL '1 day'),
    ('student1', 'student', 'hash_student1', NOW() - INTERVAL '3 days'),
    ('student2', 'student', 'hash_student2', NULL);

INSERT INTO Podjetje (username, ime, sedez, kontakt_mail)
VALUES
    ('podjetje1', 'TechCorp', 'Ljubljana', 'info@techcorp.si'),
    ('podjetje2', 'GreenSoft', 'Maribor', 'kontakt@greensoft.si');

INSERT INTO Student (username, ime, priimek, kontakt_tel, povprecna_ocena, univerza)
VALUES
    ('student1', 'Ana', 'Novak', 041123456, 8.5, 'UL FRI'),
    ('student2', 'Marko', 'Kovač', 051654321, 9.1, 'UM FERI');

INSERT INTO Pripravnistvo (trajanje, delovno_mesto, opis_dela, placilo, drzava, kraj, stevilo_mest, podjetje)
VALUES
    (3, 'Frontend Developer', 'Razvoj spletnih aplikacij v Reactu', 900, 'Slovenija', 'Ljubljana', 2, 'podjetje1'),
    (6, 'Data Analyst', 'Analiza podatkov in poročila', 1200, 'Slovenija', 'Maribor', 1, 'podjetje2'),
    (2, 'QA Tester', 'Testiranje programske opreme', 700, 'Slovenija', 'Ljubljana', 1, 'podjetje1');

INSERT INTO Prijava (status, student, pripravnistvo_id)
VALUES
    ('v obravnavi', 'student1', 1),
    ('odobrena', 'student2', 2),
    ('zavrnjena', 'student1', 3);