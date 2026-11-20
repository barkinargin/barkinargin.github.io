/* Homepage
   1. Opener: "Born in Istanbul. Blended in London. Building in Los Angeles." Each phrase lifts the dark veil off its
      part of the city, then the second line appears and the landmarks get their labels.
   2. River: a WebGL shader moves only the water (masked); buildings stay still.
   3. Landmarks are the products: Galata -> Dispatch, Tower Bridge -> Sport (the bascules lift), Griffith -> Parking.
   4. Opening a product: the landmark grows to fill the screen, then the page loads.
   Without WebGL the photo is static; with reduced motion everything appears at once. */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var root = document.documentElement, hero = document.querySelector(".hero");
  var IMG = { w: 3000, h: 1858, pad: 170, ax: 0.5, ay: 1 };   // 170px of extra sky on top; anchored to the bottom   // matches the photo's object-fit: cover; object-position: 50% 50%

  // ------------------------------------------------------------ landmarks (image coordinates)
  var LANDMARKS = [
    {
      "id": "galata",
      "name": "Galata Tower",
      "product": "Dispatch Sport",
      "line": "sport the way we used to follow it",
      "href": "/sport/",
      "bg": "#000000",
      "src": "/assets/lm/galata.webp",
      "box": [
        192,
        469,
        363,
        1082
      ],
      "poly": "47.38% 0.28%, 48.48% 4.71%, 50.69% 6.1%, 49.59% 7.67%, 48.48% 8.41%, 62.81% 21.35%, 72.45% 27.82%, 80.72% 36.14%, 91.74% 37.8%, 91.74% 38.72%, 97.25% 39.09%, 99.17% 43.53%, 99.17% 46.77%, 97.25% 47.69%, 96.42% 58.78%, 97.52% 59.43%, 97.52% 60.63%, 95.87% 61.28%, 95.87% 90.67%, 76.58% 92.33%, 71.07% 98.06%, 57.3% 99.72%, 29.75% 98.06%, 5.51% 94.82%, 4.96% 61.28%, 1.65% 60.35%, 1.65% 59.24%, 2.75% 58.32%, 2.75% 47.69%, 0.83% 46.77%, 0.83% 43.53%, 3.58% 39.09%, 7.71% 38.72%, 7.71% 37.62%, 15.98% 36.88%, 25.62% 27.82%, 35.26% 21.35%, 45.73% 8.41%, 44.63% 7.67%, 44.08% 6.1%, 46.28% 4.71%",
      "tagAt": [
        372,
        474
      ],
      "dive": [
        389,
        1062
      ],
      "note": [
        "Galata is pure nostalgia for me.",
        "So is teletext.",
        "Step back in time and follow sport",
        "the way we used to: page by page."
      ]
    },
    {
      "id": "towerbridge",
      "name": "Tower Bridge",
      "product": "The Morning Dispatch",
      "line": "AI, tech & markets every morning",
      "href": "/dispatch/",
      "bg": "#f2f3f0",
      "box": [
        975,
        340,
        290,
        220
      ],
      "tagAt": [
        1120,
        350
      ],
      "parts": [
        {
          "cls": "tb-gap",
          "src": "/assets/lm/tb-gap.webp",
          "box": [
            1036,
            504,
            168,
            21
          ]
        },
        {
          "cls": "tb-leaf-l",
          "src": "/assets/lm/tb-leaf-l.webp",
          "box": [
            1037,
            502,
            86,
            23
          ]
        },
        {
          "cls": "tb-leaf-r",
          "src": "/assets/lm/tb-leaf-r.webp",
          "box": [
            1117,
            502,
            86,
            23
          ]
        }
      ]
    },
    {
      "id": "eye",
      "name": "London Eye",
      "product": "Project 04",
      "line": "next one is in the works",
      "href": "/next/",
      "bg": "#f4f2ee",
      "src": "/assets/lm/eye.webp",
      "box": [
        1806,
        255,
        132,
        202
      ],
      "spin": 0.6428571428571429,
      "tagAt": [
        1872,
        262
      ]
    },
    {
      "id": "griffith",
      "name": "Griffith Observatory",
      "product": "Find Me a Parking Spot",
      "line": "LA street parking, block by block",
      "href": "/parking/",
      "bg": "#eef0f2",
      "src": "/assets/lm/griffith.webp",
      "box": [
        2622,
        372,
        333,
        138
      ],
      "poly": "1.8% 65.22%, 3.0% 49.28%, 9.91% 39.86%, 16.82% 49.28%, 17.42% 60.14%, 32.43% 60.14%, 33.93% 42.03%, 36.94% 23.91%, 44.44% 9.42%, 56.46% 2.17%, 68.47% 9.42%, 75.98% 23.91%, 78.08% 43.48%, 81.98% 52.9%, 84.98% 43.48%, 90.99% 40.58%, 97.0% 49.28%, 98.5% 63.77%, 99.1% 97.83%, 0.9% 97.83%",
      "tagAt": [
        2808,
        372
      ]
    }
  ];

  // ferries cut out of the photo; they cruise slowly along the river and loop
  var BOATS = [{"src": "/assets/lm/boat-ferry.webp", "box": [1870, 740, 220, 139], "dx": -620, "dy": -150, "k": 0.62, "period": 75, "offset": 0.12}, {"src": "/assets/lm/boat-speed.webp", "box": [1173, 620, 94, 49], "dx": -300, "dy": -30, "k": 0.85, "period": 32, "offset": 0.45}, {"src": "/assets/lm/boat-ferry2.webp", "box": [828, 644, 91, 103], "dx": 480, "dy": 60, "k": 1.12, "period": 85, "offset": 0.25}, {"src": "/assets/lm/boat-ferry3.webp", "box": [656, 844, 151, 79], "dx": 520, "dy": 40, "k": 1.1, "period": 95, "offset": 0.6}];
  var boatLayer = document.getElementById("boats");
  function buildBoats() {
    BOATS.forEach(function (b) { var i = new Image(); i.className = "boat"; i.alt = ""; i.src = b.src; boatLayer.appendChild(i); b.el = i; });
    if (reduce) { BOATS.forEach(function (b) { b.p = 0; }); moveBoats(0); return; }
    (function tick(now) { requestAnimationFrame(tick); if (!document.hidden) moveBoats(now / 1000); })(performance.now());
  }
  function moveBoats(t) {
    var c = cover();
    BOATS.forEach(function (b, n) {
      var p = reduce ? 0 : ((t / b.period + b.offset) % 1);
      var fade = reduce ? 1 : Math.min(1, p / 0.08, (1 - p) / 0.08);
      var bob = reduce ? 0 : Math.sin(t * 1.3 + n * 2) * 0.6;
      var x = c.ox + (b.box[0] + b.dx * p) * c.s, y = c.oy + (b.box[1] + b.dy * p) * c.s + bob;
      var k = 1 + (b.k - 1) * p, st = b.el.style;
      st.width = b.box[2] * c.s + "px"; st.height = b.box[3] * c.s + "px";
      st.transform = "translate(" + x + "px," + y + "px) scale(" + k + ")";
      st.opacity = fade;
    });
  }

  var layer = document.getElementById("landmarks");
  function cover() {
    var W = hero.clientWidth, H = hero.clientHeight, s = Math.max(W / IMG.w, H / IMG.h);
    IMG.ax = W / H < 1.15 ? 0.1 : 0.5;                 // narrow screens: keep Istanbul and London in view
    hero.style.setProperty("--ax", (IMG.ax * 100) + "%");
    return { s: s, ox: (W - IMG.w * s) * IMG.ax, oy: (H - IMG.h * s) * IMG.ay + IMG.pad * s, W: W, H: H };
  }
  function pct(v, of) { return (v / of * 100) + "%"; }

  function build() {
    LANDMARKS.forEach(function (L) {
      var el = document.createElement("div");
      el.className = "landmark" + (L.parts ? " bridge" : "") + (L.href ? "" : " soon");
      var html = "";
      if (L.src) html += '<img class="lm-img" alt="" src="' + L.src + '">';
      (L.parts || []).forEach(function (p) {
        html += '<img class="part ' + p.cls + '" alt="" src="' + p.src + '" style="left:' + pct(p.box[0] - L.box[0], L.box[2]) +
          ";top:" + pct(p.box[1] - L.box[1], L.box[3]) + ";width:" + pct(p.box[2], L.box[2]) + ";height:" + pct(p.box[3], L.box[3]) + '">';
      });
      if (L.href) {
        html += '<a class="lm-hit" href="' + L.href + '"' + (L.poly ? ' style="clip-path:polygon(' + L.poly + ')"' : "") +
          ' aria-label="' + L.name + ': ' + L.product + '"></a>';
      }
      el.innerHTML = html;
      layer.appendChild(el);
      // the label lives outside the landmark box so it can sit on its anchor point
      var tag = document.createElement(L.href ? "a" : "span");
      tag.className = "tag" + (L.href ? "" : " soon");
      if (L.href) { tag.href = L.href; tag.setAttribute("aria-label", L.product + ", at " + L.name); }
      tag.innerHTML = '<i class="dot" aria-hidden="true"></i><span class="tx"><b>' + L.product + '</b><small>' + L.name + " · " + L.line + "</small></span>";
      if (L.note) {
        tag.classList.add("has-note");
        tag.insertAdjacentHTML("beforeend", '<span class="ttx-card" aria-hidden="true"><span class="ttx-head"><span>P300</span><span>SPORT</span><span class="ttx-clock">' +
          new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }) + '</span></span><span class="ttx-band">GALATA · NOSTALGIA</span>' +
          L.note.map(function (n, i) { return '<span class="ttx-line c' + (i % 3) + '">' + n + "</span>"; }).join("") +
          '<span class="ttx-fast"><i></i><i></i><i></i><i></i></span></span>');
      }
      layer.appendChild(tag);
      L.el = el; L.tag = tag;
      if (L.spin) el.style.setProperty("--k", L.spin);

      function on() { el.classList.add("on"); tag.classList.add("on"); }
      function off() { el.classList.remove("on"); tag.classList.remove("on"); }
      [el.querySelector(".lm-hit"), tag].forEach(function (n) {
        if (!n) return;
        n.addEventListener("mouseenter", on); n.addEventListener("mouseleave", off);
        n.addEventListener("focus", on); n.addEventListener("blur", off);
        if (L.href) n.addEventListener("click", function (e) { open(e, L); });
      });
    });
    place();
    window.addEventListener("resize", place);
  }

  function place() {
    var c = cover();
    LANDMARKS.forEach(function (L) {
      var b = L.box, st = L.el.style;
      st.left = (c.ox + b[0] * c.s) + "px"; st.top = (c.oy + b[1] * c.s) + "px";
      st.width = (b[2] * c.s) + "px"; st.height = (b[3] * c.s) + "px";
      var tx = c.ox + L.tagAt[0] * c.s, ty = c.oy + L.tagAt[1] * c.s;
      L.tag.style.left = tx + "px"; L.tag.style.top = ty + "px";
      var inside = tx > 20 && tx < c.W - 20 && ty > 70 && ty < c.H - 20;
      L.tag.classList.toggle("off", !inside);
      L.tag.classList.toggle("al", tx < 190);            // keep labels inside the screen near the edges
      L.tag.classList.toggle("ar", tx > c.W - 190);
    });
  }

  // ------------------------------------------------------------ opening a product
  function grow(r, bg, href, face) {
    var ov = document.createElement("div");
    ov.className = "launch";
    ov.style.cssText = "left:" + r.left + "px;top:" + r.top + "px;width:" + r.width + "px;height:" + r.height + "px;background:" + bg;
    if (face) { var f = face.cloneNode(true); f.className = "face"; f.removeAttribute("style"); ov.appendChild(f); }
    document.body.appendChild(ov);
    ov.getBoundingClientRect(); ov.classList.add("open");
    setTimeout(function () { window.location.href = href; }, 600);
  }
  function open(e, L) {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    e.preventDefault();
    if (reduce) { window.location.href = L.href; return; }
    if (L.parts) {                     // Tower Bridge: lift the bascules first
      L.el.classList.add("open");
      setTimeout(function () { grow(L.el.getBoundingClientRect(), L.bg, L.href); }, 1700);
      return;
    }
    if (L.dive) { dive(L); return; }
    if (L.spin) {
      L.el.classList.add("spinning");
      setTimeout(function () { grow(L.el.getBoundingClientRect(), L.bg, L.href); }, 1500);
      return;
    }
    var img = L.el.querySelector(".lm-img");
    L.el.classList.add("leaving");
    grow(img.getBoundingClientRect(), L.bg, L.href, img);
  }
  // Galata: the camera flies toward one of the arched windows, then the window opens up and takes us through
  function dive(L) {
    var c = cover(), scene = document.querySelector(".scene");
    var px = c.ox + L.dive[0] * c.s, py = c.oy + L.dive[1] * c.s;          // window centre on screen
    var ww = 24 * c.s, wh = 50 * c.s;                                       // window opening size on screen
    var S = 7, T1 = 1500, cx = c.W / 2, cy = c.H / 2;
    hero.classList.add("diving");
    scene.style.transformOrigin = "0 0";
    function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
    var t0 = performance.now(), portal = null;
    (function step(now) {
      var t = Math.min(1, (now - t0) / T1), e = ease(t);
      var s = Math.exp(Math.log(S) * e);                                   // constant-feeling zoom speed
      var sx = px + (cx - px) * e, sy = py + (cy - py) * e;                 // the window glides to the centre
      scene.style.transform = "translate(" + (sx - px * s) + "px," + (sy - py * s) + "px) scale(" + s + ")";
      if (t < 1) { requestAnimationFrame(step); return; }
      // the window opening becomes the doorway
      portal = document.createElement("div");
      portal.className = "portal";
      var w = ww * S, h = wh * S;
      portal.style.cssText = "left:" + (cx - w / 2) + "px;top:" + (cy - h / 2) + "px;width:" + w + "px;height:" + h + "px;background:" + L.bg;
      portal.innerHTML = '<span class="portal-ttx">P300</span>';
      document.body.appendChild(portal);
      portal.getBoundingClientRect();
      portal.classList.add("open");
      scene.classList.add("through");
      setTimeout(function () { window.location.href = L.href; }, 700);
    })(t0);
  }
  window.addEventListener("pageshow", function () {
    document.querySelectorAll(".dive-fade").forEach(function (n) { n.remove(); });
    var sc = document.querySelector(".scene"); if (sc) { sc.classList.remove("dive", "through"); sc.style.transform = ""; }
    document.querySelectorAll(".portal").forEach(function (n) { n.remove(); }); hero.classList.remove("diving");
    document.querySelectorAll(".launch").forEach(function (n) { n.remove(); });
    LANDMARKS.forEach(function (L) { if (L.el) L.el.classList.remove("open", "leaving", "on", "spinning"); if (L.tag) L.tag.classList.remove("on"); });
  });

  // ------------------------------------------------------------ opener
  function intro() {
    var seen = false;
    try { seen = sessionStorage.getItem("seen-intro") === "1"; sessionStorage.setItem("seen-intro", "1"); } catch (e) {}
    var steps = reduce || seen
      ? [[0, "p1 p2 p3 v1 v2 v3 l2 done"]]
      : [[350, "p1"], [950, "v1"], [1600, "p2"], [2200, "v2"], [2850, "p3"], [3450, "v3"], [4200, "l2"], [5600, "done"]];
    steps.forEach(function (s) {
      setTimeout(function () { s[1].split(" ").forEach(function (c) { root.classList.add("i-" + c); }); }, s[0]);
    });
    function skip() { "p1 p2 p3 v1 v2 v3 l2 done".split(" ").forEach(function (c) { root.classList.add("i-" + c); }); }
    hero.addEventListener("click", function (e) { if (!root.classList.contains("i-done") && !e.target.closest("a")) skip(); });
    window.addEventListener("keydown", function (e) { if (e.key === "Escape" || e.key === " ") skip(); }, { once: true });
  }

  // ------------------------------------------------------------ moving river (WebGL)
  var RIVER = [
    "precision mediump float;",
    "uniform sampler2D uImg, uMask; uniform vec2 uRes, uImgSize, uAnchor; uniform float uT;",
    "void main(){",
    "  vec2 p = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);",
    "  float s = max(uRes.x / uImgSize.x, uRes.y / uImgSize.y);",
    "  vec2 disp = uImgSize * s; vec2 off = (uRes - disp) * uAnchor;",
    "  vec2 uv = (p - off) / disp;",
    "  float m = texture2D(uMask, uv).r;",
    "  float depth = mix(0.3, 1.0, clamp((uv.y - 0.3) / 0.6, 0.0, 1.0));",
    "  vec2 q = uv * vec2(1.0, 1.8);",
    "  float sw = sin(q.y * 38.0 - uT * 1.3 + sin(q.x * 6.0 + uT * 0.35) * 2.5);",
    "  float w1 = sin(q.y * 150.0 + uT * 2.0 + sin(q.x * 11.0 + uT * 0.5) * 2.4);",
    "  float w2 = sin(q.y * 80.0 - uT * 1.4 + q.x * 22.0);",
    "  float w3 = sin(q.x * 120.0 + q.y * 55.0 + uT * 2.6);",
    "  vec2 d = (vec2(w3 * 0.35 + w2 * 0.3, w1 * 0.55 + w2 * 0.35) * 0.0026 + vec2(0.0, sw) * 0.0034) * depth * m * m;",
    "  vec3 c = texture2D(uImg, uv + d).rgb;",
    "  c *= 1.0 + sw * 0.045 * m * depth;",
    "  c += pow(max(0.0, w1 * 0.5 + w3 * 0.5), 5.0) * 0.14 * m * depth * vec3(1.0, 0.92, 0.8);",
    "  gl_FragColor = vec4(c, 1.0);",
    "}"].join("\n");
  function river() {
    if (reduce) return;
    var canvas = document.getElementById("river");
    var gl = canvas.getContext("webgl", { antialias: false });
    if (!gl) return;
    var small = window.innerWidth < 900, dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    function load(src) { return new Promise(function (ok, bad) { var i = new Image(); i.onload = function () { ok(i); }; i.onerror = bad; i.src = src; }); }
    Promise.all([load(small ? "/assets/city-1600.jpg" : "/assets/city.jpg"), load("/assets/water-mask.png")]).then(function (imgs) {
      function sh(type, src) { var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
      var p = gl.createProgram();
      gl.attachShader(p, sh(gl.VERTEX_SHADER, "attribute vec2 a; void main(){ gl_Position = vec4(a, 0.0, 1.0); }"));
      gl.attachShader(p, sh(gl.FRAGMENT_SHADER, RIVER)); gl.linkProgram(p); gl.useProgram(p);
      var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      var loc = gl.getAttribLocation(p, "a"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
      imgs.forEach(function (img, i) {
        var t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, t);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        [gl.TEXTURE_WRAP_S, gl.TEXTURE_WRAP_T].forEach(function (k) { gl.texParameteri(gl.TEXTURE_2D, k, gl.CLAMP_TO_EDGE); });
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      });
      gl.uniform1i(gl.getUniformLocation(p, "uImg"), 0); gl.uniform1i(gl.getUniformLocation(p, "uMask"), 1);
      gl.uniform2f(gl.getUniformLocation(p, "uImgSize"), imgs[0].naturalWidth, imgs[0].naturalHeight);
      var uAnchor = gl.getUniformLocation(p, "uAnchor");
      var uRes = gl.getUniformLocation(p, "uRes"), uT = gl.getUniformLocation(p, "uT");
      root.classList.add("gl");
      var visible = true, t0 = performance.now();
      if ("IntersectionObserver" in window) new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(hero);
      (function frame(now) {
        requestAnimationFrame(frame);
        if (!visible || document.hidden) return;
        var w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
        if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
        gl.viewport(0, 0, w, h); gl.uniform2f(uRes, w, h); gl.uniform2f(uAnchor, IMG.ax, IMG.ay); gl.uniform1f(uT, (now - t0) / 1000);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      })(t0);
    }).catch(function () {});
  }

  buildBoats();
  build();
  intro();
  river();
})();
