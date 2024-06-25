# Aplikacja: stany magazynowe 

## Opis

Stany magazynowe to aplikacja internetowa zbudowana za pomocą Flask, która umożliwia zarządzanie zapasami. Użytkownicy mogą dodawać nowe produkty, aktualizować ich ilość, a także przeglądać aktualny stan magazynu.

## Funkcjonalności

- **Dodawanie produktów**: Umożliwia dodawanie nowych produktów do bazy danych. Info! Należy określić minimalny stan na magazynie danego produktu oraz przyporzadkować go do danej kategorii.
- **Aktualizacja produktów**: Umożliwia zwiększanie lub zmniejszanie ilości istniejących produktów.
- **Przegląd magazynu**: Wyświetla listę wszystkich produktów w magazynie. Podkresla, kiedy należy złożyć zamówienie danego produktu.
- **Śledzenie czynności**: Wyświetla wszystkie logi użytkowników

## Technologie

- Python
- Flask
- SQLAlchemy
- SQLite




## Struktura aplikacji

- `app.py` - Główny plik aplikacji.
- `templates/` - Katalog zawierający pliki HTML.
- `static/` - Katalog zawierający statyczne pliki (np. CSS).
- `models.py` - Plik zawierający definicję modelu bazy danych.
- `requirements.txt` - Plik zawierający listę zależności Pythona.

## Użycie

### Dodawanie produktu

1. Przejdź do `/add`.
2. Wypełnij formularz i kliknij "Dodaj produkt".

### Aktualizacja produktu

1. Przejdź do `/update`.
2. Wprowadź kod kreskowy produktu, ilość, datę aktualizacji oraz rodzaj operacji (dodanie/usunięcie).
3. Kliknij "Zaktualizuj".

### Przegląd magazynu
1. Pojawia się info czy magazyn ma status ok, czy trzeba coś zamówić
### Archiwum 
1. Można zobaczyć, kto co, kiedy zrobił
2. Można pobrać zakres czynności z danego czasu
