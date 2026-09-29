# mObywatel — wersja web (kopia poglądowa)

Twoja własna, prywatna aplikacja na pulpicie: **najpierw dane, potem zdjęcie**, a na końcu
karta dokumentu i portfel — wyglądem nawiązujące do mObywatela. Wszystko działa **lokalnie**:
żadnego serwera w chmurze, żadnego konta, żadnej wysyłki danych. Dane i zdjęcie zostają
w przeglądarce na Twoim komputerze.

---

## ⚠️ Zanim zaczniesz — ważne

- To **nie jest** oficjalna aplikacja mObywatel i nie ma z nią nic wspólnego.
- Wpisane dane **nie są nigdzie weryfikowane** — to kopia poglądowa, która rysuje kartę na podstawie
  tego, co sam podasz.
- Karta **nie jest dokumentem tożsamości** i nie służy do okazywania. Ma na sobie wyraźne oznaczenie
  „kopia poglądowa”.
- Program **nie łączy się z internetem**: brak analityki, brak plików cookie, brak żądań na zewnątrz
  (serwer dodatkowo wysyła nagłówek `Content-Security-Policy`, który to blokuje).
- Punkt wyjścia: publicznie udostępniony przez Ministerstwo Cyfryzacji design system mObywatela
  (29.12.2025, licencja MIT, mirror: [github.com/fajfer/mObywatel](https://github.com/fajfer/mObywatel)).
  Stamtąd pochodzą **kolory marki** (granat `#1B2B45`, akcent `#CC2430`, tło `#F3F6FB`) i układ ekranów.
  Żadne pliki graficzne rządu nie są tu użyte — ikona i wszystkie elementy są narysowane od zera.

---

## Szybki start

Potrzebujesz tylko Pythona 3 (jest w Windows, macOS i większości Linuksów).

```bash
# 1. wejdź do katalogu projektu
cd jardotexedotpng

# 2. uruchom lokalny serwer
python3 server.py
```

Otwórz **http://localhost:8000** i przejdź konfigurację: dane → zdjęcie → gotowe.

Windows: zamiast powyższego możesz kliknąć dwa razy **`start-windows.bat`**.
macOS / Linux: **`./start-mac-linux.command`** (albo `./start.sh`).

Port zajęty? `python3 server.py --port 8080`. Pracujesz nad kodem? `python3 server.py --no-cache`.

### Dlaczego nie wystarczy otworzyć `index.html` z dysku?

Plik otwarty przez `file://` działa, ale wtedy **nie da się zainstalować aplikacji** i nie działa
service worker (tryb offline). Przeglądarki wymagają do tego `http://localhost` albo `https://`.
Dlatego jest `server.py` — to 20 sekund roboty i pełna funkcjonalność.

---

## Ustaw jako aplikację na pulpicie

| System | Kroki |
|---|---|
| **Chrome / Edge** (Windows, macOS, Linux) | Otwórz `http://localhost:8000` → ikona **„Zainstaluj”** w pasku adresu (⊕ / ekranik) albo menu **⋮ → Zainstaluj „mObywatel”**. Skrót pojawi się na pulpicie, w menu Start / w Docku. |
| **Safari** (macOS 14+) | Otwórz `http://localhost:8000` → menu **Plik → Dodaj do Docka**. |
| **Android** | Chrome → menu **⋮ → Dodaj do ekranu głównego**. |
| **iPhone / iPad** | Safari → **Udostępnij → Dodaj do ekranu początkowego**. |
| **Firefox** | Firefox na komputerze nie obsługuje instalowania PWA — działa normalna karta (offline również). |

Po zainstalowaniu aplikacja otwiera się w osobnym oknie, bez paska adresu, ma własną ikonę
i działa offline. W samej aplikacji jest też przycisk **„Zainstaluj”** (ekran startowy i Ustawienia).

> Uwaga: instalacja nie zadziała wewnątrz podglądu osadzonego w ramce (`iframe`) innego serwisu —
> otwórz adres bezpośrednio w przeglądarce.

---

## Hosting — jak to postawić prywatnie

Aplikacja jest w 100% statyczna, więc hostować ją można wszędzie. Ale uwaga na jedną pułapkę:

> ### ⛔ GitHub Pages nie umie być prywatne
> Nawet gdy repozytorium jest **prywatne**, opublikowana strona jest **publiczna** — a jej adres
> (`drpeer.github.io/jardotexedotpng`) łatwo zgadnąć. Prywatne Pages istnieją wyłącznie w planie
> **GitHub Enterprise Cloud** (płatnym, dla organizacji). Plan Pro/Team tego nie zmienia.
> Źródło: [GitHub Docs](https://docs.github.com/en/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site).

Dlatego w repozytorium jest gotowy przepis na **naprawdę prywatny** hosting — [`deploy/PRYWATNY-HOSTING.md`](deploy/PRYWATNY-HOSTING.md):

| Opcja | Prywatne? | Koszt | Co daje |
|---|---|---|---|
| **Cloudflare Pages + Access** (zalecane) | ✅ tak | 0 zł | adres `*.pages.dev` albo własna domena, logowanie **kodem e-mail** (Zero Trust Free do 50 osób), zero zmian w kodzie |
| **Lokalnie + tunel** | ✅ tak | 0 zł | `python3 server.py --auth anna:haslo --tunnel` — dostęp z telefonu przez losowy adres + hasło |
| **Tylko dom / LAN / Tailscale** | ✅ tak | 0 zł | serwer w ogóle nie trafia do internetu |
| GitHub Pages (szablon w `deploy/`) | ❌ **nie** | 0 zł | wyłączony domyślnie — publikuje dopiero po świadomym wklejeniu szablonu i włączeniu zmiennej `ALLOW_PUBLIC_PAGES` |

### Własny serwer z bramką hasła

```bash
python3 server.py --auth anna:dlugie-haslo --open      # hasło (HTTP Basic), dostęp lokalnie
python3 server.py --auth anna:dlugie-haslo             # + dostęp z telefonu w tej samej sieci Wi-Fi
python3 server.py --auth anna:dlugie-haslo --tunnel    # + dostęp z dowolnego miejsca (cloudflared)
```

### Sprawdź, czy Twoja strona naprawdę jest prywatna

```bash
python3 tools/check_private.py https://twoj-adres.pages.dev
# ✅ CHRONIONE — serwer odmawia dostępu bez hasła/logowania.
# ❌ PUBLICZNE — każdy może otworzyć aplikację.
```

### Publikowanie gdziekolwiek (Cloudflare Pages, Netlify, Vercel, własny serwer)

```bash
python3 tools/make_dist.py --zip   # tworzy dist/ oraz dist.zip (do wgrania na hosting)
python3 server.py --dist           # podgląd dokładnie tej paczki na localhost
```

`dist/` zawiera też plik `_headers` z polityką CSP (`default-src 'self'`), czyli hostowana strona
technicznie nie może łączyć się z żadnym zewnętrznym serwerem.

**Ważne:** nawet na publicznym hostingu dane użytkownika nie wyciekają — siedzą w `localStorage`
przeglądarki i nigdzie nie są wysyłane. Bramka hostingu chroni *aplikację*, nie *dane*.

---

## Co potrafi

**Konfiguracja (kreator)**
- Ekran startowy z wyjaśnieniem, po co są dane.
- **Dane:** imię, nazwisko, PESEL, obywatelstwo, opcjonalnie seria i numer dowodu oraz adres.
  PESEL jest sprawdzany lokalnie (suma kontrolna), a **data urodzenia i płeć wyliczają się same**.
  Walidacja pokazuje błędy przy polu, Enter = „Dalej”.
- **Zdjęcie:** z pliku, metodą przeciągnij-i-upuść, **ze schowka (Ctrl+V)** albo z **kamery**.
  Kadrowanie okrągłe z zoomem (suwak, kółko myszy), obrotem ±90° i przesuwaniem palcem/myszą.
  Zapisywane jako 512×512 JPEG — bez wysyłania czegokolwiek na zewnątrz.
- **Gotowe:** podgląd karty + instrukcja instalacji na pulpicie.

**Portfel**
- Karta dokumentu (styl mDowodu: czerwony gradient, zdjęcie, dane, flaga) z wyraźnym znaczkiem
  „kopia poglądowa”.
- Sekcje: *Dane osobowe* i *Bezpieczeństwo*.
- Zakładki: **Portfel / Moje dane / Ustawienia**.
- Edycja danych i zmiana zdjęcia w każdej chwili.
- **Eksport / import kopii** (plik JSON) oraz **usunięcie wszystkich danych** jednym przyciskiem.
- Działa offline (service worker), ma manifest PWA, ikony i skróty pulpitu.
- Pełna obsługa klawiatury, etykiety ARIA, respektowanie `prefers-reduced-motion`.

---

## Prywatność — gdzie trafiają dane

| Co | Gdzie | Kto ma dostęp |
|---|---|---|
| Dane osobowe | `localStorage` tej przeglądarki (`mobywatel.web.v1`) | tylko Ty, na tym komputerze |
| Zdjęcie | `localStorage` (`mobywatel.web.photo.v1`, JPEG 512×512) | tylko Ty, na tym komputerze |
| Kopie zapasowe | pliki JSON, które sam wyeksportujesz | Ty (uwaga: JSON **nie jest** szyfrowany — trzymaj go bezpiecznie) |

Danych **nie da się odzyskać** po wyczyszczeniu danych przeglądarki, po użyciu trybu prywatnego
albo po zmianie profilu przeglądarki. Rób kopie (Ustawienia → *Eksportuj kopię*).

Profilaktyka: jeśli nie chcesz trzymać prawdziwego numeru PESEL w przeglądarce, wpisz **dowolną
liczbę 11-cyfrową z poprawną sumą kontrolną** — wystarczy do testów (np. `44051401458`).
Pole PESEL jest wymagane tylko dlatego, że z niego wyliczana jest data urodzenia i płeć.

---

## Struktura projektu

```
index.html                 cała aplikacja (HTML + CSS + JS, bez zależności)
manifest.webmanifest       manifest PWA (nazwa, ikony, skróty, kolory)
sw.js                      service worker — tryb offline
server.py                  serwer lokalny: MIME dla PWA, CSP, hasło (--auth), tunel (--tunnel)
deploy/PRYWATNY-HOSTING.md  przewodnik: jak wystawić aplikację prywatnie (Cloudflare Access itd.)
_headers / _redirects      nagłówki CSP i przekierowania dla hostingów statycznych
deploy/github-pages-public.yml   szablon workflow GitHub Pages (publiczne!) — wyłączony domyślnie
start-windows.bat          uruchomienie jednym kliknięciem (Windows)
start-mac-linux.command    uruchomienie jednym kliknięciem (macOS / Linux)
start.sh                   to samo dla terminala
icon.svg                   ikona wektorowa
icon-192.png / icon-512.png / icon-maskable-512.png / apple-touch-icon*.png / favicon.ico
tools/make_icons.py        generator ikon (Pillow) — gdy chcesz zmienić kolor lub znak
tools/smoke-test.js        test logiki w jsdom (walidacja, PESEL, przejścia, zapis, usuwanie)
tools/crop-test.js         test geometrii kadrowania i eksportu zdjęcia
tools/make_dist.py         buduje dist/ — paczkę gotową do wrzucenia na hosting
tools/check_private.py     sprawdza, czy strona za bramką logowania jest naprawdę prywatna
```

Aplikacja nie ma żadnych zależności produkcyjnych — to jeden plik HTML plus zasoby PWA.

---

## Testy

```bash
npm install        # jednorazowo (jedyna zależność: jsdom, tylko do testów)
npm test           # oba zestawy: logika + kadrowanie
# albo pojedynczo:
npm run test:smoke   # walidacja, PESEL, przejścia widoków, zapis w localStorage
npm run test:crop    # geometria kadrowania i eksport JPEG 512x512
```

Oba skrypty kończą się `WSZYSTKO OK`. `crop-test.js` sprawdza m.in., że zapisany kadr
pokrywa całe 512×512, nie zniekształca proporcji i jest zgodny z tym, co widać w podglądzie.

---

## Rozwiązywanie problemów

| Objaw | Przyczyna / rozwiązanie |
|---|---|
| Brak przycisku „Zainstaluj” | Strona otwarta przez `file://`, w trybie prywatnym albo już zainstalowana. Uruchom `python3 server.py` i wejdź na `http://localhost:8000`. |
| „Nie udało się uruchomić aparatu” | Kamera wymaga `http://localhost` lub `https://` i zgody przeglądarki. Wybierz zdjęcie z pliku — efekt jest ten sam. |
| Dane zniknęły | Wyczyszczono dane przeglądarki / tryb prywatny / inny profil. Wczytaj kopię JSON albo wpisz dane ponownie. |
| Zmieniłem kod, a widzę starą wersję | Service worker trzyma kopię. Podnieś numer `CACHE` w `sw.js` (np. `v2`) albo uruchom serwer z `--no-cache` i odśwież z Ctrl+Shift+R. |
| Port 8000 zajęty | `python3 server.py --port 8080`. |
| Chcę wejść z telefonu w tej samej sieci | Serwer domyślnie nasłuchuje na `0.0.0.0`; w konsoli wypisze adres LAN, np. `http://192.168.0.10:8000`. Użyj `--auth`, jeśli sieć nie jest w pełni zaufana. |
| Chcę dostęp z dowolnego miejsca | `python3 server.py --auth uzytkownik:haslo --tunnel` (wymaga `cloudflared`). Na stałe: Cloudflare Pages + Access, patrz `deploy/PRYWATNY-HOSTING.md`. |
| „Zainstaluję to na GitHub Pages i będzie prywatne” | Nie będzie. Patrz sekcja **Hosting** — GitHub Pages publikuje publicznie nawet z prywatnego repo. |

---

## Licencja i atrybucja

- Kod tego projektu: **MIT** (patrz `LICENSE`).
- Paleta i układ inspirowane design systemem mObywatela, opublikowanym przez Ministerstwo Cyfryzacji
  29.12.2025 na licencji MIT. mObywatel jest znakiem towarowym Skarbu Państwa Polskiego —
  użyty tu wyłącznie opisowo, w projekcie hobbystycznym/edukacyjnym, bez sugerowania powiązań.
- Projekt nie zawiera kodu ani zasobów z repozytorium rządowego poza wartościami kolorów marki.

**To nie jest dokument. To nie jest oficjalna aplikacja. Nie okazuj tego nikomu jako dowodu.**
