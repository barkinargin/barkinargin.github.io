/* Homepage effects
   1. River: a WebGL shader animates only the water in the city photo (masked), so the buildings stay still.
   2. Waterline: a second shader draws moving water in front of the phone's base, with a wavy, glinting edge.
   3. Launch: tapping an app icon grows it to fill the screen, then opens the page.
   Everything degrades: no WebGL -> static photo and CSS water; reduced motion -> no animation. */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var stage = document.querySelector(".stage");

  // ------------------------------------------------------------ tiny WebGL helper
  function gl3(canvas) {
    var gl = canvas.getContext("webgl", { premultipliedAlpha: true, antialias: false, alpha: true });
    if (!gl) return null;
    return gl;
  }
  function program(gl, frag) {
    var vs = "attribute vec2 a; void main(){ gl_Position = vec4(a, 0.0, 1.0); }";
    function sh(type, src) {
      var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    }
    var p = gl.createProgram();
    gl.attachShader(p, sh(gl.VERTEX_SHADER, vs)); gl.attachShader(p, sh(gl.FRAGMENT_SHADER, frag));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    gl.useProgram(p);
    var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    var loc = gl.getAttribLocation(p, "a"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    return p;
  }
  function texture(gl, img, unit, repeat) {
    var t = gl.createTexture(); gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
    var wrap = repeat ? gl.REPEAT : gl.CLAMP_TO_EDGE;
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, wrap); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, wrap);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    return t;
  }
  function load(src) {
    return new Promise(function (ok, bad) { var i = new Image(); i.onload = function () { ok(i); }; i.onerror = bad; i.src = src; });
  }
  function fit(canvas, dpr) {
    var w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  }

  var RIVER = [
    "precision mediump float;",
    "uniform sampler2D uImg, uMask; uniform vec2 uRes, uImgSize, uAnchor; uniform float uT;",
    "void main(){",
    "  vec2 p = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);",
    "  float s = max(uRes.x / uImgSize.x, uRes.y / uImgSize.y);",
    "  vec2 disp = uImgSize * s; vec2 off = (uRes - disp) * uAnchor;",
    "  vec2 uv = (p - off) / disp;",
    "  float m = texture2D(uMask, uv).r;",
    "  float depth = mix(0.35, 1.0, clamp((uv.y - 0.4) / 0.5, 0.0, 1.0));", // nearer water moves more
    "  vec2 q = uv * vec2(1.0, 1.8);",
    "  float w1 = sin(q.y * 190.0 + uT * 1.7 + sin(q.x * 12.0 + uT * 0.4) * 2.0);",
    "  float w2 = sin(q.y * 95.0 - uT * 1.1 + q.x * 24.0);",
    "  float w3 = sin(q.x * 140.0 + q.y * 60.0 + uT * 2.3);",
    "  vec2 d = vec2(w3 * 0.35 + w2 * 0.25, w1 * 0.6 + w2 * 0.4) * 0.0015 * depth * m * m;",
    "  vec3 c = texture2D(uImg, uv + d).rgb;",
    "  c += pow(max(0.0, w1 * 0.5 + w3 * 0.5), 6.0) * 0.09 * m * depth;", // moving glints
    "  gl_FragColor = vec4(c, 1.0);",
    "}"].join("\n");

  var FRONT = [
    "precision mediump float;",
    "uniform sampler2D uTex; uniform vec2 uRes; uniform float uT, uEdge, uDpr;",
    "void main(){",
    "  vec2 p = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);",
    "  float x = p.x / uRes.x;",
    "  float edge = uEdge + (sin(p.x / (26.0 * uDpr) + uT * 2.2) * 2.0 + sin(p.x / (9.0 * uDpr) - uT * 3.1) * 0.8",
    "             + sin(p.x / (55.0 * uDpr) - uT * 1.3) * 1.6) * uDpr;",
    "  float below = smoothstep(edge - 1.2 * uDpr, edge + 1.2 * uDpr, p.y);",
    "  float side = smoothstep(0.0, 0.26, x) * (1.0 - smoothstep(0.74, 1.0, x));",
    "  vec2 uv = p / (620.0 * uDpr); uv.y *= 1.7;",
    "  uv.x += sin(uv.y * 40.0 + uT * 1.5) * 0.004 + uT * 0.008;",
    "  uv.y += sin(uv.x * 30.0 - uT * 1.2) * 0.005;",
    "  vec3 c = texture2D(uTex, uv).rgb * 0.9;",
    "  float hl = exp(-pow((p.y - edge) / (1.5 * uDpr), 2.0));",                       // glint on the waterline
    "  float shade = smoothstep(edge, edge + 8.0 * uDpr, p.y) * (1.0 - smoothstep(edge + 8.0 * uDpr, edge + 40.0 * uDpr, p.y));",
    "  c = c * (1.0 - 0.2 * shade) + hl * 0.55;",
    "  float a = below * side * 0.84 + hl * side * 0.65;",
    "  gl_FragColor = vec4(c * a, a);",
    "}"].join("\n");

  function startWater() {
    if (reduce || !stage) return;
    var riverCanvas = document.getElementById("river"), frontCanvas = document.getElementById("waterfront");
    var small = window.innerWidth < 900;
    var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    Promise.all([load(small ? "/assets/city-1600.jpg" : "/assets/city.jpg"), load("/assets/water-mask.png"), load("/assets/water-tile.jpg")])
      .then(function (imgs) {
        var g1 = gl3(riverCanvas), g2 = gl3(frontCanvas);
        if (!g1 || !g2) throw new Error("no webgl");
        var p1 = program(g1, RIVER);
        texture(g1, imgs[0], 0, false); texture(g1, imgs[1], 1, false);
        g1.uniform1i(g1.getUniformLocation(p1, "uImg"), 0); g1.uniform1i(g1.getUniformLocation(p1, "uMask"), 1);
        g1.uniform2f(g1.getUniformLocation(p1, "uImgSize"), imgs[0].naturalWidth, imgs[0].naturalHeight);
        g1.uniform2f(g1.getUniformLocation(p1, "uAnchor"), 0.5, 0.58);
        var u1 = { res: g1.getUniformLocation(p1, "uRes"), t: g1.getUniformLocation(p1, "uT") };

        var p2 = program(g2, FRONT);
        texture(g2, imgs[2], 0, true);
        g2.uniform1i(g2.getUniformLocation(p2, "uTex"), 0);
        var u2 = { res: g2.getUniformLocation(p2, "uRes"), t: g2.getUniformLocation(p2, "uT"),
                   edge: g2.getUniformLocation(p2, "uEdge"), dpr: g2.getUniformLocation(p2, "uDpr") };

        document.documentElement.classList.add("gl");
        var visible = true, t0 = performance.now();
        if ("IntersectionObserver" in window) {
          new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(stage);
        }
        function frame(now) {
          requestAnimationFrame(frame);
          if (!visible || document.hidden) return;
          var t = (now - t0) / 1000;
          fit(riverCanvas, dpr); g1.viewport(0, 0, riverCanvas.width, riverCanvas.height);
          g1.uniform2f(u1.res, riverCanvas.width, riverCanvas.height); g1.uniform1f(u1.t, t);
          g1.drawArrays(g1.TRIANGLE_STRIP, 0, 4);
          fit(frontCanvas, dpr); g2.viewport(0, 0, frontCanvas.width, frontCanvas.height);
          g2.uniform2f(u2.res, frontCanvas.width, frontCanvas.height); g2.uniform1f(u2.t, t);
          g2.uniform1f(u2.edge, 16 * dpr); g2.uniform1f(u2.dpr, dpr);
          g2.clearColor(0, 0, 0, 0); g2.clear(g2.COLOR_BUFFER_BIT);
          g2.drawArrays(g2.TRIANGLE_STRIP, 0, 4);
        }
        requestAnimationFrame(frame);
      })
      .catch(function () { document.documentElement.classList.add("nogl"); });
  }

  // ------------------------------------------------------------ clickable landmarks
  // box: x, y, width, height in the 3000 x 1688 city image; poly: the outline, in % of the box (also the click area)
  var IMG = { w: 3000, h: 1688, anchorX: 0.5, anchorY: 0.58 };
  var LANDMARKS = [
    { id: "galata", name: "Galata Tower", label: "Dispatch", href: "/dispatch/", bg: "#f2f3f0", src: "/assets/lm/galata.webp",
      box: [333, 492, 312, 905],
      poly: "49.04% 0.44%, 52.88% 4.2%, 52.88% 6.74%, 51.6% 8.84%, 64.74% 20.77%, 79.17% 31.82%, 87.18% 35.36%, 92.31% 36.91%, 89.1% 37.68%, 89.74% 44.53%, 98.72% 45.64%, 97.44% 47.85%, 94.87% 48.95%, 94.87% 57.79%, 98.72% 58.56%, 97.44% 60.77%, 93.27% 61.66%, 92.95% 99.45%, 85.58% 99.56%, 61.54% 95.47%, 3.85% 91.38%, 5.45% 89.28%, 5.45% 61.22%, 1.28% 60.55%, 1.92% 58.34%, 4.49% 57.46%, 4.49% 49.06%, 1.92% 46.3%, 3.85% 45.08%, 9.94% 44.53%, 9.94% 37.68%, 7.69% 36.91%, 12.5% 35.69%, 23.72% 31.82%, 35.9% 20.77%, 46.79% 8.84%, 45.51% 6.74%, 45.51% 4.2%" }
  ];
  var layer = document.getElementById("landmarks"), hero = document.querySelector(".hero");
  function buildLandmarks() {
    if (!layer) return;
    LANDMARKS.forEach(function (L) {
      var el = document.createElement("div");
      el.className = "landmark"; el.dataset.id = L.id;
      el.innerHTML = '<img class="lm-img" alt="" src="' + L.src + '">' +
        '<a class="lm-hit" href="' + L.href + '" data-bg="' + L.bg + '" style="clip-path: polygon(' + L.poly + ')" aria-label="' + L.name + ': open ' + L.label + '"></a>' +
        '<span class="lm-label" aria-hidden="true"><small>' + L.name + '</small><b>' + L.label + ' \u2192</b></span>';
      layer.appendChild(el);
      L.el = el;
      var hit = el.querySelector(".lm-hit");
      ["mouseenter", "focus"].forEach(function (ev) { hit.addEventListener(ev, function () { el.classList.add("on"); }); });
      ["mouseleave", "blur"].forEach(function (ev) { hit.addEventListener(ev, function () { el.classList.remove("on"); }); });
    });
    placeLandmarks();
    window.addEventListener("resize", placeLandmarks);
    if (!reduce) setTimeout(function () {       // one gentle hint that these are clickable
      LANDMARKS.forEach(function (L) { L.el.classList.add("hint"); setTimeout(function () { L.el.classList.remove("hint"); }, 1400); });
    }, 3400);
  }
  function placeLandmarks() {   // same "cover" maths as the hero photo (object-position 50% 58%)
    var W = hero.clientWidth, H = hero.clientHeight, s = Math.max(W / IMG.w, H / IMG.h);
    var ox = (W - IMG.w * s) * IMG.anchorX, oy = (H - IMG.h * s) * IMG.anchorY;
    LANDMARKS.forEach(function (L) {
      var b = L.box, st = L.el.style;
      st.left = (ox + b[0] * s) + "px"; st.top = (oy + b[1] * s) + "px";
      st.width = (b[2] * s) + "px"; st.height = (b[3] * s) + "px";
    });
  }
  buildLandmarks();

  // ------------------------------------------------------------ app launch transition
  function launch(e) {
    var a = e.currentTarget;
    if (reduce || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button !== 0) return;
    e.preventDefault();
    var lm = a.closest(".landmark");
    var icon = lm ? lm.querySelector(".lm-img") : a.querySelector(".icon"), r = icon.getBoundingClientRect(), cs = getComputedStyle(icon);
    var ov = document.createElement("div");
    ov.className = "launch";
    ov.style.cssText = "left:" + r.left + "px;top:" + r.top + "px;width:" + r.width + "px;height:" + r.height + "px;border-radius:" +
      cs.borderTopLeftRadius + ";background:" + (a.dataset.bg || "#f2f3f0");
    ov.style.setProperty("--w", getComputedStyle(stage).getPropertyValue("--w"));
    var face = icon.cloneNode(true);
    face.className = icon.className + " face";
    if (lm) { ov.style.borderRadius = "0"; ov.style.boxShadow = "none"; face.style.objectFit = "contain"; }
    ov.appendChild(face);
    document.body.appendChild(ov);
    icon.style.visibility = "hidden";
    ov.getBoundingClientRect(); // commit start state
    ov.classList.add("open");
    setTimeout(function () { window.location.href = a.href; }, 560);
  }
  document.querySelectorAll("a.app, a.lm-hit").forEach(function (a) { a.addEventListener("click", launch); });
  window.addEventListener("pageshow", function (e) {   // coming back: clean up
    document.querySelectorAll(".launch").forEach(function (n) { n.remove(); });
    document.querySelectorAll("a.app .icon, .lm-img").forEach(function (n) { n.style.visibility = ""; });
  });

  startWater();
})();
