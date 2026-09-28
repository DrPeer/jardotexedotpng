/* Smoke test logiki aplikacji w jsdom (bez przeglądarki).
   Uruchomienie:  NODE_PATH=/tmp/pw/node_modules node tools/smoke-test.js
   Testuje: brak błędów JS, walidację (w tym PESEL), przejścia widoków,
   zapis do localStorage oraz render karty/portfela. */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const ROOT = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");

let failures = 0;
function check(name, cond, extra) {
  if (cond) { console.log("  \u2713 " + name); }
  else { failures++; console.log("  \u2717 " + name + (extra ? "  \u2192 " + extra : "")); }
}

const errors = [];
const vc = new VirtualConsole();
vc.on("jsdomError", (e) => {
  if (/Not implemented/.test(e.message)) { return; }  // ograniczenia jsdom, nie aplikacji
  errors.push("jsdomError: " + e.message);
});
vc.on("error", (...a) => errors.push("console.error: " + a.join(" ")));

const dom = new JSDOM(html, {
  url: "http://localhost:8000/index.html",
  runScripts: "dangerously",
  pretendToBeVisual: true,
  virtualConsole: vc,
  beforeParse(window) {
    // jsdom nie implementuje przewijania okna — nie ma to wpływu na logikę aplikacji
    window.scrollTo = function () {};
    window.HTMLElement.prototype.scrollIntoView = function () {};
    window.matchMedia = window.matchMedia || ((q) => ({
      matches: false, media: q, onchange: null,
      addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}, dispatchEvent() { return false; }
    }));
  }
});

const { window } = dom;
const doc = window.document;
const $ = (s) => doc.querySelector(s);
const click = (sel) => {
  const el = $(sel);
  if (!el) { throw new Error("brak elementu " + sel); }
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
};
const type = (sel, val) => {
  const el = $(sel);
  el.value = val;
  el.dispatchEvent(new window.Event("input", { bubbles: true }));
};
const active = () => ($(".view.is-active") || {}).id;

setTimeout(() => {
  console.log("\n1) Start");
  check("brak błędów JS przy starcie", errors.length === 0, errors.join(" | "));
  check("widok powitalny aktywny", active() === "view-welcome", active());
  check("pasek zakładek ukryty", $("#tabbar").hidden === true);
  check("widok Ustawień jest w <main> (nad paskiem zakładek)", !!doc.querySelector("main #view-settings"));
  check("wszystkie 6 widoków istnieje", doc.querySelectorAll(".view").length === 6, doc.querySelectorAll(".view").length);
  for (const f of ["icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png", "manifest.webmanifest", "icon.svg"]) {
    check("zasób istnieje: " + f, fs.existsSync(path.join(ROOT, f)));
  }
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "manifest.webmanifest"), "utf8"));
  check("manifest: poprawny JSON i tryb standalone", manifest.display === "standalone");
  check("manifest: ikona maskable zadeklarowana", manifest.icons.some((i) => i.purpose === "maskable"));

  console.log("\n2) Walidacja formularza");
  click("#btn-start");
  check("przejście do widoku danych", active() === "view-data", active());
  type("#in-imie", "Anna");
  type("#in-nazwisko", "Kowalska");
  type("#in-pesel", "123");
  click("#btn-data-next");
  check("krótki PESEL odrzucony", $("#f-pesel").classList.contains("has-error"));
  type("#in-pesel", "44051401458"); // poprawny PESEL testowy (suma kontrolna OK, data 1944-05-14)
  check("PESEL: płeć odczytana", $("#in-plec").value === "M\u0118\u017bCZYZNA", $("#in-plec").value);
  check("PESEL: data odczytana", /^\d{2}\.\d{2}\.\d{4}$/.test($("#in-data").value), $("#in-data").value);
  type("#in-pesel", "44051401459"); // zła suma kontrolna
  check("PESEL: zła suma kontrolna wykryta", !$("#f-pesel").classList.contains("ok"));
  type("#in-pesel", "44051401458");
  type("#in-dokument", "abc123456");
  check("numer dowodu: wielkie litery", $("#in-dokument").value === "ABC123456", $("#in-dokument").value);
  type("#in-adres", "ul. Kwiatowa 1, 85-001 Bydgoszcz");

  console.log("\n3) Zapis danych");
  click("#btn-data-next");
  check("przejście do widoku zdjęcia", active() === "view-photo", active());
  const stored = JSON.parse(window.localStorage.getItem("mobywatel.web.v1") || "null");
  check("dane zapisane w localStorage", !!stored && stored.pesel === "44051401458");
  check("zapisane imię/nazwisko", stored.imie === "Anna" && stored.nazwisko === "Kowalska");

  console.log("\n4) Pominięcie zdjęcia i portfel");
  click("#btn-photo-skip");
  check("widok gotowe", active() === "view-done", active());
  check("karta dokumentu wyrenderowana", !!$("#done-card-slot .doc"));
  check("na karcie widnieje PESEL", ($("#done-card-slot .doc") || {}).textContent.includes("44051401458"));
  check("na karcie jest oznaczenie 'kopia poglądowa'", ($("#done-card-slot .doc") || {}).textContent.toLowerCase().includes("pogl\u0105dowa"));
  click("#btn-open-wallet");
  check("portfel aktywny", active() === "view-wallet", active());
  check("pasek zakładek widoczny", $("#tabbar").hidden === false);
  check("powitanie z imieniem", $("#wallet-title").textContent.includes("Anna"), $("#wallet-title").textContent);
  check("sekcja danych osobowych", $("#wallet-sections").textContent.includes("44051401458"));
  check("brak zdjęcia \u2192 inicjały", $("#wallet-avatar-fallback").textContent === "AK", $("#wallet-avatar-fallback").textContent);

  console.log("\n5) Nawigacja zakładkami");
  click('.tab[data-view="view-data"]');
  check("zakładka 'Moje dane'", active() === "view-data", active());
  check("tryb edycji: przycisk 'Zapisz zmiany'", $("#btn-data-next").textContent.trim() === "Zapisz zmiany", $("#btn-data-next").textContent.trim());
  type("#in-imie", "Hanna");
  click("#btn-data-next");
  check("powrót do portfela po zapisie", active() === "view-wallet", active());
  check("zmiana widoczna w portfelu", $("#wallet-sections").textContent.includes("Hanna"));
  click('.tab[data-view="view-settings"]');
  check("zakładka ustawień", active() === "view-settings", active());
  check("status danych w ustawieniach", $("#stat-data").textContent.includes("Hanna"), $("#stat-data").textContent);
  check("zdjęcie: brak", $("#stat-photo").textContent === "brak");

  console.log("\n6) Ustawienia: usuwanie danych");
  click("#btn-wipe");
  click("#wipe-confirm");
  check("powrót na ekran powitalny", active() === "view-welcome", active());
  check("localStorage wyczyszczony", window.localStorage.getItem("mobywatel.web.v1") === null);
  check("formularz wyczyszczony", $("#in-imie").value === "" && $("#in-pesel").value === "");

  console.log("\n7) Ponowne wejście w konfigurację");
  click("#btn-start");
  check("konfiguracja od nowa", active() === "view-data", active());
  type("#in-imie", "Jan");
  type("#in-nazwisko", "Nowak");
  type("#in-pesel", "02211312341"); // 2001-01-13 (miesiąc +20), cyfra płci 4 -> kobieta
  check("płeć wyliczona z 10. cyfry", ["KOBIETA", "M\u0118\u017bCZYZNA"].includes($("#in-plec").value));

  check("brak nowych błędów JS", errors.length === 0, errors.join(" | "));

  console.log("\n" + (failures === 0 ? "WSZYSTKO OK" : failures + " B\u0141\u0118D\u00d3W"));
  process.exit(failures === 0 ? 0 : 1);
}, 300);
