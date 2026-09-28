/* Test geometrii kadrowania i eksportu zdjęcia.
   Sprawdza, że podgląd (transform CSS) i zapisywany kadr (drawImage na canvas)
   korzystają z tej samej matematyki i że zdjęcie zawsze pokrywa cały kwadrat.

   Uruchomienie: NODE_PATH=/tmp/pw/node_modules node tools/crop-test.js   */
const fs = require("fs");
const path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const ROOT = path.resolve(__dirname, "..");
const html = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");

let failures = 0;
const check = (name, cond, extra) => {
  if (cond) { console.log("  \u2713 " + name); }
  else { failures++; console.log("  \u2717 " + name + (extra !== undefined ? "  \u2192 " + extra : "")); }
};

const IMG_W = 800, IMG_H = 600;    // krajobrazowe zdjęcie źródłowe
let lastDraw = null;
let toDataURLCalled = 0;

const vc = new VirtualConsole();
vc.on("jsdomError", (e) => { if (!/Not implemented/.test(e.message)) { console.log("  ! " + e.message); } });

const dom = new JSDOM(html, {
  url: "http://localhost:8000/index.html",
  runScripts: "dangerously",
  pretendToBeVisual: true,
  virtualConsole: vc,
  beforeParse(window) {
    window.scrollTo = function () {};
    // jsdom nie liczy layoutu — udajemy realną szerokość kadru (CSS: max-width 300px)
    Object.defineProperty(window.Element.prototype, "clientWidth", { get() { return 300; }, configurable: true });
    window.HTMLElement.prototype.scrollIntoView = function () {};
    window.matchMedia = (q) => ({ matches: false, media: q, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {}, dispatchEvent() { return false; } });

    // --- zaślepki: obraz o znanych wymiarach -----------------------------------
    const makeImg = () => {
      const img = window.document.createElement("img");
      Object.defineProperty(img, "naturalWidth", { get: () => IMG_W, configurable: true });
      Object.defineProperty(img, "naturalHeight", { get: () => IMG_H, configurable: true });
      let src = "";
      Object.defineProperty(img, "src", {
        get: () => src,
        set: (v) => {
          src = v;
          setTimeout(() => {
            if (typeof img.onload === "function") { img.onload(); }
            else { img.dispatchEvent(new window.Event("load")); }
          }, 0);
        },
        configurable: true
      });
      return img;
    };
    window.Image = function Image() { return makeImg(); };

    window.URL.createObjectURL = () => "blob:podglad";
    window.URL.revokeObjectURL = () => {};

    // --- zaślepka canvas z prawdziwą macierzą transformacji -------------------
    // Dzięki temu sprawdzamy, gdzie obraz NAPRAWDĘ trafia na 512x512 canvasie.
    window.HTMLCanvasElement.prototype.getContext = function () {
      let m = [1, 0, 0, 1, 0, 0];               // a,b,c,d,e,f
      const stack = [];
      const mul = (A, B) => [
        A[0] * B[0] + A[2] * B[1], A[1] * B[0] + A[3] * B[1],
        A[0] * B[2] + A[2] * B[3], A[1] * B[2] + A[3] * B[3],
        A[0] * B[4] + A[2] * B[5] + A[4], A[1] * B[4] + A[3] * B[5] + A[5]
      ];
      const pt = (x, y) => [m[0] * x + m[2] * y + m[4], m[1] * x + m[3] * y + m[5]];
      return {
        fillStyle: "#fff", imageSmoothingQuality: "high",
        save() { stack.push(m.slice()); },
        restore() { m = stack.pop() || [1, 0, 0, 1, 0, 0]; },
        scale(x, y) { m = mul(m, [x, 0, 0, y, 0, 0]); },
        translate(x, y) { m = mul(m, [1, 0, 0, 1, x, y]); },
        rotate(r) { const c = Math.cos(r), s = Math.sin(r); m = mul(m, [c, s, -s, c, 0, 0]); },
        fillRect() {},
        drawImage(img, dx, dy, dw, dh) {
          const c = pt(dx + dw / 2, dy + dh / 2);
          const corners = [pt(dx, dy), pt(dx + dw, dy), pt(dx, dy + dh), pt(dx + dw, dy + dh)];
          lastDraw = {
            cx: c[0], cy: c[1], dw, dh,
            x0: Math.min(...corners.map(p => p[0])), x1: Math.max(...corners.map(p => p[0])),
            y0: Math.min(...corners.map(p => p[1])), y1: Math.max(...corners.map(p => p[1])),
            ratio: dw / dh
          };
        }
      };
    };
    window.HTMLCanvasElement.prototype.toDataURL = function () {
      toDataURLCalled++;
      return "data:image/jpeg;base64,TESTOWE";
    };
  }
});

const { window } = dom;
const doc = window.document;
const $ = (s) => doc.querySelector(s);
const click = (sel) => $(sel).dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
const type = (sel, val) => { const el = $(sel); el.value = val; el.dispatchEvent(new window.Event("input", { bubbles: true })); };
const cssTransform = () => $("#crop-img").style.transform;

// wyciągnij liczby z transformacji CSS: translate(tx,ty) rotate(deg) scale(s)
function parseTransform(t) {
  const m = /translate\(([-\d.]+)px,\s*([-\d.]+)px\)\s*rotate\(([-\d.]+)deg\)\s*scale\(([\d.]+)\)/.exec(t);
  if (!m) { return null; }
  return { tx: +m[1], ty: +m[2], rot: +m[3], s: +m[4] };
}

setTimeout(() => {
  // przejdź onboarding do widoku zdjęcia
  click("#btn-start");
  type("#in-imie", "Anna"); type("#in-nazwisko", "Kowalska"); type("#in-pesel", "44051401458");
  click("#btn-data-next");
  check("jesteśmy w widoku zdjęcia", $(".view.is-active").id === "view-photo", $(".view.is-active").id);

  // wczytaj plik-obraz
  const file = new window.File([new Uint8Array([1, 2, 3])], "foto.jpg", { type: "image/jpeg" });
  const input = $("#file-input");
  Object.defineProperty(input, "files", { value: [file], configurable: true });
  try { input.dispatchEvent(new window.Event("change", { bubbles: true })); }
  catch (err) { console.log("  ! wyjątek przy wczytywaniu pliku: " + err.message); }

  setTimeout(() => {
    const box = $("#cropper").clientWidth || 300;
    check("pokazano kadrowanie", $("#photo-crop").hidden === false);
    check("ukryto wybór pliku", $("#photo-pick").hidden === true);

    // 1) bez obrotu, zoom 1 — skala "cover"
    let t = parseTransform(cssTransform());
    check("transformacja ma oczekiwany format", !!t, cssTransform());
    const sCover = Math.max(box / IMG_W, box / IMG_H);
    check("skala cover (800x600)", Math.abs(t.s - sCover) < 1e-6, t.s + " vs " + sCover);
    check("środek obrazu = środek kwadratu", Math.abs(t.tx - (box / 2 - IMG_W / 2)) < 1e-6 && Math.abs(t.ty - (box / 2 - IMG_H / 2)) < 1e-6, t.tx + "," + t.ty);

    // 2) obrót 90° — obraz nadal pokrywa kwadrat (szerokość >= box)
    click("#btn-rot-r");
    setTimeout(() => {
      t = parseTransform(cssTransform());
      check("obrót 90° zapisany", t.rot === 90, t.rot);
      const bw = IMG_W * t.s, bh = IMG_H * t.s;           // bbox po obrocie 90°: bh x bw
      check("po obrocie zdjęcie pokrywa kadr w pionie", bh >= box - 1e-6, bh + " >= " + box);
      check("po obrocie zdjęcie pokrywa kadr w poziomie", bw >= box - 1e-6, bw + " >= " + box);
      check("obrót: bez rozciągania (skala cover po obrocie)", Math.abs(t.s - Math.max(box / IMG_H, box / IMG_W)) < 1e-6, t.s);

      // 3) zoom 200% i eksport — geometria musi zgadzać się z podglądem
      const zoom = $("#zoom");
      zoom.value = "2";
      zoom.dispatchEvent(new window.Event("input", { bubbles: true }));
      t = parseTransform(cssTransform());
      check("zoom podwojony", Math.abs(t.s - 2 * Math.max(box / IMG_H, box / IMG_W)) < 1e-6, t.s);

      click("#btn-photo-save");
      const d = lastDraw;
      check("eksport narysował obraz", !!d);
      const k = 512 / box;                                  // skala kadru: podgląd -> plik
      check("eksport: kadr pokrywa cały plik 512x512 (oś X)", d.x0 <= 1e-6 && d.x1 >= 512 - 1e-6, d.x0.toFixed(2) + ".." + d.x1.toFixed(2));
      check("eksport: kadr pokrywa cały plik 512x512 (oś Y)", d.y0 <= 1e-6 && d.y1 >= 512 - 1e-6, d.y0.toFixed(2) + ".." + d.y1.toFixed(2));
      check("eksport: środek zgodny ze środkiem kadru w podglądzie",
        Math.abs(d.cx - (box / 2 + (t.tx + IMG_W / 2 - box / 2)) * k) < 0.01 &&
        Math.abs(d.cy - 256) < 0.01, d.cx.toFixed(2) + "," + d.cy.toFixed(2));
      check("eksport: brak zniekształceń (proporcje 800:600 zachowane)",
        Math.abs(d.ratio - IMG_W / IMG_H) < 1e-6, d.dw + "x" + d.dh);
      check("eksport: zoom 200% przeniesiony 1:1", Math.abs(d.dw - IMG_W * t.s) < 1e-6, d.dw + " vs " + IMG_W * t.s);
      check("zapisano zdjęcie (canvas.toDataURL wywołane)", toDataURLCalled > 0, toDataURLCalled);

      // 4) zdjęcie trafia do localStorage i na kartę
      const photo = window.localStorage.getItem("mobywatel.web.photo.v1");
      check("zdjęcie w localStorage", !!photo && photo.startsWith("data:image/jpeg"));
      check("widok gotowe", $(".view.is-active").id === "view-done", $(".view.is-active").id);
      check("karta zawiera <img> ze zdjęciem", !!$("#done-card-slot .doc img.doc__photo"));

      console.log("\n" + (failures === 0 ? "WSZYSTKO OK" : failures + " B\u0141\u0118D\u00d3W"));
      process.exit(failures === 0 ? 0 : 1);
    }, 60);
  }, 60);
}, 200);

