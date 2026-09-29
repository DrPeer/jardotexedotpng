# Prywatny hosting — przewodnik

Cel: mieć aplikację dostępną z dowolnego urządzenia, ale **tylko dla Ciebie** (i najwyżej kilku
znajomych osób). Poniżej szczera mapa możliwości i gotowe przepisy.

---

## 1. Najkrótsza prawda o GitHub Pages

**Nie da się zrobić prywatnej strony na GitHub Pages.** I to nie jest kwestia planu Pro:

| Plan | Pages z prywatnego repo? | Czy strona może być prywatna? |
|---|---|---|
| Free (konto osobiste) | nie (repo musi być publiczne) | nie |
| Pro / Team | tak | **nie — strona jest publiczna** |
| Enterprise Cloud (organizacja) | tak | tak, z kontrolą dostępu Pages |

Repo prywatne ≠ strona prywatna. Adres `drpeer.github.io/jardotexedotpng` byłby **publiczny dla
całego internetu**, a jego nazwa jest przewidywalna — nie trzeba go „znaleźć”, wystarczy zgadnąć.
Dotyczy to także repozytoriów internal.

Źródła: [GitHub Docs — Changing the visibility of your GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site),
[GitHub Docs — About GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages).

Wniosek: jeśli chcesz „prywatnie”, hosting musi być **inny niż GitHub Pages**. Poniżej trzy drogi,
wszystkie darmowe.

> Uwaga: nawet na publicznej stronie **dane użytkowników nie wyciekają** — aplikacja trzyma je
> w `localStorage` przeglądarki i nigdzie ich nie wysyła. Publiczny hosting oznaczałby tylko tyle,
> że ktoś inny mógłby otworzyć *twoją* aplikację i wpisać *swoje* dane. Ale skoro to ma być prywatne,
> zróbmy to prywatnie.

---

## 2. Które rozwiązanie wybrać?

| Opcja | Czy naprawdę prywatne? | Koszt | Login | Wymaga |
|---|---|---|---|---|
| **A. Cloudflare Pages + Access** | tak (bramka przed stroną) | 0 zł (do 50 osób) | kod e-mail (OTP) lub Google/GitHub | konto Cloudflare |
| **B. Lokalnie + tunel z hasłem** | tak (hasło + losowy adres) | 0 zł | hasło HTTP Basic | `cloudflared` |
| **C. Tylko w domu (LAN / Tailscale)** | tak (nie ma go w internecie) | 0 zł | hasło lub VPN | nic |
| D. GitHub Pages | **nie** | 0 zł | brak | konto GitHub |

---

## Opcja A — Cloudflare Pages + Cloudflare Access (zalecana)

Efekt: adres `https://twoja-nazwa.pages.dev`, za którym stoi bramka Cloudflare. Bez zalogowania
**nikt** nie zobaczy nawet kodu strony. Zero zmian w kodzie aplikacji.

### Skrót — 5 kroków

| # | Co robisz | Gdzie |
|---|---|---|
| 1 | `python3 tools/make_dist.py --zip` → powstaje **`dist.zip`** | terminal u Ciebie |
| 2 | Zakładasz darmowe konto | <https://dash.cloudflare.com/sign-up> |
| 3 | **Workers & Pages → Create → Pages → Upload assets** → nazwa projektu → wrzucasz `dist.zip` → **Deploy** | dash.cloudflare.com |
| 4 | **Zero Trust → Access → Applications → Add → Self-hosted** → domena `twoja-nazwa.pages.dev` → polityka **Allow** z Twoim e-mailem → **One-time PIN** | <https://one.dash.cloudflare.com> |
| 5 | Sprawdzasz: `python3 tools/check_private.py https://twoja-nazwa.pages.dev` → ma pokazać **✅ CHRONIONE** | terminal u Ciebie |

Krok 4 jest tym, który czyni stronę prywatną. **Zanim go wykonasz, adres jest publiczny** — nie
wysyłaj go nikomu wcześniej. Szczegóły poniżej.

### A1. Zbuduj paczkę do wysłania

```bash
python3 tools/make_dist.py --zip   # tworzy dist/ ORAZ dist.zip (71 kB)
```

`dist.zip` to dokładnie to, co wrzucisz do Cloudflare — w archiwum `index.html` leży w korzeniu,
bez podkatalogu nadrzędnego (Cloudflare tego wymaga).

### A2. Opublikuj

1. Wejdź na <https://dash.cloudflare.com/sign-up> i utwórz darmowe konto (wystarczy e-mail).
2. Lewe menu: **Workers & Pages → Create → Pages → Upload assets**
   (w nowszym interfejsie: **Create application → Pages → Upload assets**).
3. Nazwa projektu, np. `moj-portfel` — ta nazwa trafi do adresu `moj-portfel.pages.dev`.
4. Wrzuć **`dist.zip`** (albo przeciągnij całą zawartość katalogu `dist/`) i kliknij **Deploy**.
5. Strona jest online — ale **na razie publiczna**. Wykonaj A3 **zanim** komukolwiek podasz adres.

> Wskazówka: adres projektu poznasz od razu po wdrożeniu — wygląda jak
> `https://moj-portfel.pages.dev` (ewentualnie z losowym sufiksem, np. `moj-portfel-4f2.pages.dev`).
> Użyj dokładnie tego adresu w kroku A3.

### A3. Zamknij ją bramką Access (to ten krok czyni stronę prywatną)

1. Wejdź na <https://one.dash.cloudflare.com> — to panel **Zero Trust**. Przy pierwszym wejściu
   zostaniesz poproszony o **nazwę zespołu (team name)** i wybór planu: wybierz **Free**
   (obejmuje do 50 użytkowników, nie wymaga płatności; czasem poprosi o kartę, ale plan Free
   nic nie kosztuje).
2. **Access → Applications → Add an application → Self-hosted**.
3. **Application domain**: wpisz pełny adres z kroku A2, np. `moj-portfel.pages.dev`.
   Pole ścieżki (**path**) zostaw puste — ma chronić całą aplikację.
4. Sekcja **Policies → Add a policy**:
   - **Policy name**: `tylko ja`,
   - **Action**: **Allow**,
   - **Configure rules → Include → Emails** → Twój adres e-mail
     (dodaj kolejne wpisy, jeśli chcesz wpuścić kogoś bliskiego).
5. **Authentication / Login methods**: zostaw **One-time PIN** — to znaczy „wpisz e-mail, dostaniesz
   6-cyfrowy kod”. Jeśli wolisz, możesz dodać logowanie przez Google.
6. **Next → Save**. Następnie w ustawieniach tej aplikacji ustaw **Session Duration**
   (np. 24 godziny) — decyduje, jak często Cloudflare ma pytać ponownie.

**Nie widzisz opcji „Enable access policy” w Settings projektu Pages?** Nie szkodzi — to starsze
miejsce, które Cloudflare przeniosło do panelu Zero Trust. Ścieżka z punktu 1–6 działa zawsze.

> Pierwszy test: otwórz adres w **oknie prywatnym**. Powinien pojawić się ekran Cloudflare
> z prośbą o e-mail i kod — a **nie** Twoja aplikacja. Jeśli widzisz aplikację, bramka jeszcze
> nie obejmuje tego adresu (wróć do punktu 3).

### A4. Domknij obejścia (ważne!)

Cloudflare chroni **tylko te adresy**, które wskażesz jako aplikacje. Zabezpiecz wszystkie:

- **Podglądy wdrożeń.** Każde wdrożenie dostaje dodatkowy, tymczasowy adres —
  jeśli nie chronisz `*.moj-portfel.pages.dev`, ktoś może wejść tamtędy. Dodaj drugą aplikację
  Access z hostname typu **wildcard**: `*.<nazwa-projektu>.pages.dev`.
- **Własna domena.** Jeśli kiedyś podepniesz `portfel.twojadomena.pl`, ta domena to **osobny**
  adres — dodaj dla niej kolejną aplikację Access (albo dodaj oba adresy do tej samej).
- **Alias produkcyjny.** W Cloudflare Pages ustaw w **Settings → Builds & deployments** jedną
  stałą gałąź produkcyjną, żeby nie powstawały nieoczekiwane adresy podglądowe.

Po każdej zmianie powtarzaj test z okna prywatnego — to 5 sekund, a łapie 90% wpadek.

### A5. Sprawdź, czy naprawdę jest prywatne

```bash
python3 tools/check_private.py https://moj-portfel.pages.dev
```

Skrypt mówi wprost: `CHRONIONE` / `PUBLICZNE`. Możesz też otworzyć adres w **oknie prywatnym** —
powinien pojawić się ekran logowania Cloudflare, a nie aplikacja.

### Aktualizacje

Po zmianach w kodzie:

```bash
python3 tools/make_dist.py --zip        # nowe dist.zip
```

…a potem w Cloudflare: **Workers & Pages → Twój projekt → Create deployment → Upload assets**
i wrzuć nowy `dist.zip`. (Bezpośredni upload nie ma historii — każde wgranie to nowe wdrożenie.)

Wolisz automatyzację? W Cloudflare: **Pages → Create → Connect to Git**, wskaż to repozytorium,
a jako katalog wyjściowy podaj `dist` (albo dodaj krok budujący `tools/make_dist.py`).
Wtedy każdy `git push` aktualizuje stronę, a **bramka Access z A3 nadal działa** — dostęp mają
wyłącznie osoby z Twojej listy.

---

## Opcja B — Lokalnie + tunel z hasłem (najszybsza, działa od razu)

Aplikacja działa na Twoim komputerze, a tunel wystawia ją pod losowym, nieodgadywalnym adresem
`https://losowa-nazwa.trycloudflare.com`, za którym stoi hasło.

```bash
# 1. zainstaluj cloudflared (jednorazowo)
#    Windows:  winget install --id Cloudflare.cloudflared
#    macOS:    brew install cloudflared
#    Linux:    https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

# 2. uruchom aplikację z hasłem i tunelem
python3 server.py --auth anna:bardzo-tajne-haslo --tunnel --open
```

W konsoli pojawi się adres do otwarcia na telefonie lub w pracy. Poprosi o hasło
(`anna` + hasło, które ustawisz). Zamknięcie okna = koniec dostępu.

- Wybierz hasło **długie** (min. 12 znaków) — to jedyna bramka.
- Adres tunelu zmienia się przy każdym uruchomieniu.
- Tunel to wygoda, nie forteca: przy stałym używaniu lepsza jest opcja A (prawdziwy login).

---

## Opcja C — Tylko w domu (najbezpieczniejsza)

Serwer nie jest w ogóle wystawiony do internetu — dostęp mają tylko urządzenia w Twojej sieci.

```bash
python3 server.py --auth anna:haslo --open
# w konsoli pojawi się np. http://192.168.0.10:8000 — otwórz to na telefonie w tej samej sieci Wi-Fi
```

Chcesz mieć dostęp z zewnątrz, ale bez publicznego adresu? Dołóż **Tailscale** (darmowe dla
użytku osobistego): instalujesz na komputerze i telefonie, włączasz `tailscale serve` i łączysz się
adresem z Twojej prywatnej sieci VPN — nikt z internetu go nie widzi.

---

## Opcja D — GitHub Pages (świadomie publiczna)

Jeśli uznasz, że jednak może być publiczna — **paczka jest już gotowa**: katalog `docs/` na gałęzi
`main` (zbudowany przez `python3 tools/make_dist.py --docs`). Wystarczy:
Settings → General → Change visibility → **Public**, a potem
Settings → **Pages** → *Deploy from a branch* → `main` + `/docs` → **Save**.
Adres: `https://drpeer.github.io/jardotexedotpng/`. Z powrotem na Private = strona gaśnie (plan Free).

Wariant alternatywny (przez Actions) leży w gotowym szablonie
[`deploy/github-pages-public.yml`](github-pages-public.yml) — z instrukcją w nagłówku pliku.
Jest **wyłączony domyślnie**: publikuje dopiero, gdy sam wkleisz go do `.github/workflows/`,
ustawisz zmienną `ALLOW_PUBLIC_PAGES=true` i ręcznie uruchomisz workflow, wpisując `TAK`
w polu potwierdzenia. Zanim to zrobisz, przeczytaj sekcję 1 — ta strona będzie dostępna dla każdego.

Alternatywa bez GitHuba: podepnij repozytorium do Cloudflare Pages (Workers & Pages →
Create → Pages → Connect to Git) i dodaj bramkę Access z sekcji A3 — wtedy każdy `git push`
aktualizuje stronę, a dostęp nadal mają tylko osoby z Twojej listy.

---

## Ściąga: co jest chronione w tej aplikacji

- **Dane osobowe i zdjęcie** nigdy nie opuszczają przeglądarki (localStorage, brak żądań sieciowych).
- **Bramka hostingu** chroni *aplikację*: kto jej nie przejdzie, nie zobaczy nawet jej kodu.
- **Hasło Basic Auth** w `server.py` chroni dostęp do serwera lokalnego/tunelu.
- Kopia JSON (Ustawienia → Eksportuj) **nie jest szyfrowana** — trzymaj ją jak dokument tożsamości.
