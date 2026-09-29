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

### A1. Zbuduj paczkę do wysłania

```bash
python3 tools/make_dist.py         # tworzy dist/
```

### A2. Opublikuj

1. Wejdź na <https://dash.cloudflare.com> i utwórz darmowe konto.
2. **Workers & Pages → Create → Pages → Upload assets**.
3. Nazwa projektu, np. `moj-portfel` (ta nazwa trafi do adresu).
4. Przeciągnij **całą zawartość katalogu `dist/`** (nie sam katalog!) i kliknij **Deploy**.
5. Strona jest już online — ale **publiczna**. Zabezpiecz ją w następnym kroku, zanim komukolwiek
   ją wyślesz.

### A3. Zamknij ją bramką Access

1. Wejdź na <https://one.dash.cloudflare.com> (Zero Trust; przy pierwszym wejściu wybierz plan
   **Free** — obejmuje 50 użytkowników i nie wymaga płatności).
2. **Access → Applications → Add an application → Self-hosted**.
3. **Application domain** → wpisz `moj-portfel.pages.dev` (dokładnie swoją nazwę).
   Ścieżka: pozostaw pustą (chroni całą stronę).
4. **Policies → Add a policy**:
   - nazwa: `tylko ja`,
   - akcja: **Allow**,
   - **Include → Emails** → Twój adres e-mail (dodaj kolejne, jeśli chcesz wpuścić kogoś bliskiego).
5. **Authentication**: zostaw **One-time PIN** (kod wysyłany mailem). Jeśli wolisz, dodaj Google.
6. Zapisz (**Save**), a następnie w ustawieniach aplikacji ustaw **Session Duration**
   (np. 24 godziny — jak często ma pytać ponownie).

### A4. Domknij obejścia (ważne!)

Cloudflare chroni tylko te adresy, które wpiszesz jako aplikacje. Zabezpiecz **wszystkie**:

- powtórz A3 dla domeny własnej, jeśli kiedyś podepniesz `portfel.twojadomena.pl`,
- powtórz A3 dla **podglądów**: `*.<nazwa-projektu>.pages.dev` (typ hostname: wildcard) —
  inaczej ktoś może wejść przez tymczasowy adres wdrożenia.

### A5. Sprawdź, czy naprawdę jest prywatne

```bash
python3 tools/check_private.py https://moj-portfel.pages.dev
```

Skrypt mówi wprost: `CHRONIONE` / `PUBLICZNE`. Możesz też otworzyć adres w **oknie prywatnym** —
powinien pojawić się ekran logowania Cloudflare, a nie aplikacja.

### Aktualizacje

Po zmianach w kodzie: `python3 tools/make_dist.py` i ponownie **Upload assets** (albo podłącz
repozytorium Git w Cloudflare Pages, jeśli wolisz publikowanie automatyczne po `git push`).

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

Jeśli kiedyś uznasz, że jednak może być publiczna, w repozytorium leży gotowy szablon
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
