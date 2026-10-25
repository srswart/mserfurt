(function () {
  "use strict";

  var READ_KEY = "ms_erfurt_read_sections";
  var UNSEAL_KEY = "ms_erfurt_unsealed";
  var SIZE_KEY = "ms_erfurt_font_size";
  var MARKS_KEY = "ms_erfurt_marks";
  var ACCENT_KEY = "ms_erfurt_accent";
  var VARIANT_KEY = "ms_erfurt_variant";

  function readList() {
    try {
      var parsed = JSON.parse(localStorage.getItem(READ_KEY) || "[]");
      return Array.isArray(parsed) ? parsed : [];
    } catch (err) {
      return [];
    }
  }

  function saveRead(ids) {
    localStorage.setItem(READ_KEY, JSON.stringify(ids));
  }

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch];
    });
  }

  function clamp(n, lo, hi) {
    return Math.max(lo, Math.min(hi, n));
  }

  function initAccent() {
    var saved = localStorage.getItem(ACCENT_KEY) || "#E0644B";
    document.documentElement.style.setProperty("--accent", saved);
    document.querySelectorAll("[data-accent]").forEach(function (btn) {
      btn.classList.toggle("on", btn.getAttribute("data-accent").toLowerCase() === saved.toLowerCase());
      btn.addEventListener("click", function () {
        var color = btn.getAttribute("data-accent");
        localStorage.setItem(ACCENT_KEY, color);
        document.documentElement.style.setProperty("--accent", color);
        document.querySelectorAll("[data-accent]").forEach(function (other) {
          other.classList.toggle("on", other === btn);
        });
      });
    });
  }

  function initMenus() {
    document.querySelectorAll(".menu-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var header = btn.closest(".site-header");
        var open = header.classList.toggle("nav-open");
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      });
    });
  }

  function setVariant(variant) {
    var word = variant === "lost" ? "lost" : "proud";
    localStorage.setItem(VARIANT_KEY, word);
    document.querySelectorAll("[data-variant-word]").forEach(function (el) {
      el.textContent = word;
    });
    var inline = document.getElementById("inline-variant-btn");
    if (inline) inline.textContent = word;
    document.querySelectorAll("[data-pick]").forEach(function (btn) {
      var on = btn.getAttribute("data-pick") === word;
      btn.classList.toggle("on", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  window.toggleContestedVariant = function () {
    var current = localStorage.getItem(VARIANT_KEY) || "proud";
    setVariant(current === "proud" ? "lost" : "proud");
  };

  window.setContestedVariant = setVariant;

  function initReader() {
    var root = document.querySelector(".reader");
    if (!root) return;
    var size = parseInt(localStorage.getItem(SIZE_KEY) || "21", 10);
    if (isNaN(size)) size = 21;
    var marks = localStorage.getItem(MARKS_KEY) !== "0";
    var read = readList();

    function paint() {
      size = clamp(size, 17, 27);
      root.style.setProperty("--read-size", size + "px");
      root.classList.toggle("marks", marks);
      document.querySelectorAll("[data-marks-toggle]").forEach(function (btn) {
        btn.classList.toggle("on", marks);
        btn.setAttribute("aria-pressed", marks ? "true" : "false");
      });
      localStorage.setItem(SIZE_KEY, String(size));
      localStorage.setItem(MARKS_KEY, marks ? "1" : "0");
    }

    var smaller = document.getElementById("smaller");
    var larger = document.getElementById("larger");
    if (smaller) smaller.addEventListener("click", function () { size -= 2; paint(); });
    if (larger) larger.addEventListener("click", function () { size += 2; paint(); });
    document.querySelectorAll("[data-marks-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function () { marks = !marks; paint(); });
    });
    paint();
    setVariant(localStorage.getItem(VARIANT_KEY) || "proud");
    document.querySelectorAll("[data-pick]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setVariant(btn.getAttribute("data-pick"));
      });
    });

    var toc = document.querySelector(".toc");
    var tocBtn = document.getElementById("open-contents");
    if (tocBtn && toc) {
      tocBtn.addEventListener("click", function () {
        var open = toc.classList.toggle("open");
        tocBtn.classList.toggle("on", open);
      });
      toc.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", function () { toc.classList.remove("open"); });
      });
      var closeToc = document.getElementById("close-contents");
      if (closeToc) {
        closeToc.addEventListener("click", function () {
          toc.classList.remove("open");
          tocBtn.classList.remove("on");
        });
      }
    }

    var ticking = false;
    function updateRead() {
      ticking = false;
      var line = window.innerHeight * 0.62;
      var current = null;
      document.querySelectorAll("section.edition-section").forEach(function (section) {
        var rect = section.getBoundingClientRect();
        if (rect.top <= line && rect.bottom > 80) current = section;
        var seen = rect.top < line && (rect.bottom < window.innerHeight * 0.92 || (line - rect.top) / Math.max(rect.height, 1) > 0.4);
        if (seen && section.id.indexOf("sec-") === 0 && read.indexOf(section.id) < 0) {
          read.push(section.id);
        }
      });
      var finale = document.getElementById("sec-7");
      if (finale) {
        var end = finale.getBoundingClientRect();
        if (end.bottom <= window.innerHeight + 48 && end.top < window.innerHeight * 0.7) {
          if (read.indexOf("sec-7") < 0) read.push("sec-7");
          localStorage.setItem(UNSEAL_KEY, "1");
        }
      }
      saveRead(read);
      if (current) {
        var bar = document.getElementById("read-progress");
        if (bar) bar.style.width = (current.getAttribute("data-progress") || "0") + "%";
        document.querySelectorAll(".toc a[href^='#']").forEach(function (link) {
          if (link.getAttribute("href") === "#" + current.id) link.setAttribute("aria-current", "true");
          else link.removeAttribute("aria-current");
        });
        var pill = document.getElementById("vellum-pill");
        var folio = current.getAttribute("data-folio");
        if (pill && folio) {
          pill.href = "/viewer?folio=" + folio;
          var img = pill.querySelector("img");
          if (img) img.src = "/assets/folios/" + folio + "_thumb.jpg";
          var label = pill.querySelector("span");
          if (label) label.textContent = "On the vellum · " + (current.getAttribute("data-short") || folio);
        }
      }
    }
    function schedule() {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(updateRead);
      }
    }
    window.addEventListener("scroll", schedule, { passive: true });
    updateRead();
  }

  function initFolios() {
    var group = document.querySelector("[data-folio-filters]");
    if (!group) return;
    var leaves = document.querySelectorAll(".leaf");
    group.querySelectorAll("[data-filter]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var filter = btn.getAttribute("data-filter");
        group.querySelectorAll("[data-filter]").forEach(function (other) {
          var on = other === btn;
          other.classList.toggle("on", on);
          other.setAttribute("aria-pressed", on ? "true" : "false");
        });
        leaves.forEach(function (leaf) {
          var match = filter === "all" || leaf.getAttribute("data-" + filter) === "1";
          leaf.classList.toggle("dim", !match);
        });
      });
    });
  }

  function initColophon() {
    var seal = document.getElementById("seal-view");
    if (!seal) return;
    var read = readList();
    var unsealed = localStorage.getItem(UNSEAL_KEY) === "1" || read.indexOf("sec-7") >= 0;
    var work = document.getElementById("work-view");
    var count = 0;
    for (var i = 1; i <= 7; i += 1) {
      var on = read.indexOf("sec-" + i) >= 0;
      if (on) count += 1;
      var pip = document.getElementById("pip-" + i);
      if (pip && on) pip.classList.add("on");
    }
    var label = document.getElementById("read-count");
    if (label) label.textContent = count + " of 7 sections read";

    function showWork() {
      localStorage.setItem(UNSEAL_KEY, "1");
      seal.hidden = true;
      work.hidden = false;
      window.scrollTo(0, 0);
    }
    if (unsealed) showWork();

    var arm = document.getElementById("arm-seal");
    var confirm = document.getElementById("seal-confirm");
    var disarm = document.getElementById("keep-sealed");
    var breakBtn = document.getElementById("break-seal");
    if (arm && confirm) {
      arm.addEventListener("click", function () {
        arm.hidden = true;
        confirm.hidden = false;
      });
    }
    if (disarm && arm && confirm) {
      disarm.addEventListener("click", function () {
        confirm.hidden = true;
        arm.hidden = false;
      });
    }
    if (breakBtn) breakBtn.addEventListener("click", showWork);
  }

  function openingPair(id) {
    var match = /^f(\d+)([rv])$/.exec(id);
    if (!match) return { left: null, right: id };
    var n = parseInt(match[1], 10);
    var pad = function (k) { return (k < 10 ? "0" : "") + k; };
    if (match[2] === "r") {
      return { left: n > 1 ? "f" + pad(n - 1) + "v" : null, right: id };
    }
    return { left: id, right: n < 17 ? "f" + pad(n + 1) + "r" : null };
  }

  function initViewer() {
    var app = document.querySelector(".viewer-app");
    if (!app) return;
    fetch("/data/site_data.json")
      .then(function (res) { return res.json(); })
      .then(boot)
      .catch(function () {
        var hint = document.querySelector(".stage-hint");
        if (hint) hint.textContent = "The folio catalogue could not be loaded.";
      });

    function boot(data) {
      var params = new URLSearchParams(window.location.search);
      var state = {
        id: params.get("folio") || "f04r",
        zoom: 1,
        panX: 0,
        panY: 0,
        mode: "leaf",
        surface: "weathered",
        tab: "apparatus",
        layers: { dmg: false, conf: false, hand: false, dips: false },
        dragging: false
      };
      if (!data.folios.some(function (f) { return f.id === state.id; })) state.id = data.folios[0].id;

      var stage = document.getElementById("stage");
      var transform = document.getElementById("stage-transform");
      var frame = document.getElementById("leaf-frame");
      var drag = null;

      function folio(id) {
        return data.folios.filter(function (f) { return f.id === id; })[0] || null;
      }

      function applyTransform() {
        transform.style.transform = "translate(" + state.panX + "px, " + state.panY + "px) scale(" + state.zoom + ")";
        transform.style.transition = state.dragging ? "none" : "transform 0.25s ease";
        var label = document.getElementById("zoom-label");
        if (label) label.textContent = Math.round(state.zoom * 100) + "%";
        var rect = document.getElementById("minimap-rect");
        var img = frame.querySelector("img");
        if (!rect || !img) return;
        var z = state.zoom;
        var navW = Math.min(100, 100 / z);
        var navH = Math.min(100, 100 / z);
        var w = img.offsetWidth || 400;
        var h = img.offsetHeight || 600;
        var navL = clamp(50 - navW / 2 - (state.panX / (w * z)) * 100, 0, 100 - navW);
        var navT = clamp(50 - navH / 2 - (state.panY / (h * z)) * 100, 0, 100 - navH);
        rect.style.left = navL + "%";
        rect.style.top = navT + "%";
        rect.style.width = navW + "%";
        rect.style.height = navH + "%";
      }

      function setZoom(next) {
        state.zoom = clamp(Math.round(next * 100) / 100, 0.5, 5);
        applyTransform();
      }

      function render() {
        var leaf = folio(state.id);
        var idx = data.folios.indexOf(leaf);
        var clean = state.surface === "clean";
        var title = document.getElementById("folio-title");
        var sub = document.getElementById("folio-sub");
        if (title) title.textContent = "Folio " + leaf.label + (state.mode === "opening" ? " · opening" : "");
        if (sub) {
          var side = leaf.id.slice(-1) === "r" ? "recto" : "verso";
          sub.textContent = side + " · " + (idx + 1) + " of " + data.folios.length;
        }
        document.getElementById("mode-leaf").classList.toggle("on", state.mode === "leaf");
        document.getElementById("mode-opening").classList.toggle("on", state.mode === "opening");
        document.getElementById("mode-weathered").classList.toggle("on", !clean);
        document.getElementById("mode-clean").classList.toggle("on", clean);
        document.getElementById("mode-leaf").setAttribute("aria-pressed", state.mode === "leaf" ? "true" : "false");
        document.getElementById("mode-opening").setAttribute("aria-pressed", state.mode === "opening" ? "true" : "false");

        if (state.mode === "opening") {
          var pair = openingPair(leaf.id);
          var spread = !clean && data.spreads.filter(function (s) {
            return s.left_folio === pair.left && s.right_folio === pair.right;
          })[0];
          if (spread) {
            frame.innerHTML = '<img src="' + esc(spread.img) + '" alt="Opening ' + esc(pair.left) + " – " + esc(pair.right) + '" draggable="false">';
          } else {
            var left = pair.left ? folio(pair.left) : null;
            var right = pair.right ? folio(pair.right) : null;
            var srcOf = function (item) { return clean ? item.clean_img : item.img; };
            frame.innerHTML = '<div class="opening">' +
              (left ? '<img src="' + esc(srcOf(left)) + '" alt="Folio ' + esc(left.label) + '" draggable="false">' : "") +
              '<div class="gutter" aria-hidden="true"></div>' +
              (right ? '<img src="' + esc(srcOf(right)) + '" alt="Folio ' + esc(right.label) + '" draggable="false">' : "") +
              "</div>";
          }
        } else {
          var src = clean ? leaf.clean_img : leaf.img;
          var classes = ["overlays"];
          if (state.layers.dmg) classes.push("show-dmg");
          if (state.layers.conf) classes.push("show-conf");
          if (state.layers.hand) classes.push("show-hand");
          if (state.layers.dips) classes.push("show-dips");
          var html = '<img src="' + esc(src) + '" alt="Folio ' + esc(leaf.label) + '" draggable="false">';
          html += '<div class="' + classes.join(" ") + '">';
          leaf.conf_lines.forEach(function (c) {
            html += '<div class="ov-conf" title="Line ' + c.n + " · confidence " + esc(c.pct) + '" style="left:2.2%;top:' + c.top + "%;height:2.4%;width:" + c.w + "%;background:" + esc(c.col) + ';opacity:0.9"></div>';
            html += '<div class="ov-band" style="left:10.5%;right:9%;top:' + c.top + "%;height:3.3%;background:" + esc(c.band) + '"></div>';
          });
          leaf.dmg_boxes.forEach(function (d) {
            html += '<div class="ov-dmg" title="' + esc(d.n) + '" style="left:' + d.x + "%;top:" + d.y + "%;width:" + d.bw + "%;height:" + d.bh + "%;border:" + esc(d.border) + '"></div>';
          });
          leaf.lac_labels.forEach(function (l) {
            html += '<span class="ov-lac" style="left:' + l.x + "%;top:" + l.y + '%">' + esc(l.t) + "</span>";
          });
          leaf.hand_lines.forEach(function (h) {
            html += '<div class="ov-hand" style="left:10.5%;right:12%;top:' + h.top + '%;height:3.3%;border-bottom:2px dotted #8FB3D1"></div>';
            html += '<span class="ov-hand ov-hand-label" style="top:' + h.top + '%">' + esc(h.t) + "</span>";
          });
          leaf.dip_markers.forEach(function (p) {
            html += '<span class="ov-dip" title="Quill re-dipped · ' + esc(p.w) + '" style="left:9.4%;top:' + p.top + '%;width:7px;height:7px;border-radius:50%;background:#231D17;box-shadow:0 0 0 2px #E8C77A"></span>';
          });
          html += "</div>";
          frame.innerHTML = html;
        }

        var mini = document.getElementById("minimap-img");
        if (mini) mini.src = leaf.thumb;
        document.getElementById("dmg-count").textContent = leaf.dmg + " damage spans on this leaf";
        document.getElementById("conf-count").textContent = leaf.lines + " lines read";
        document.getElementById("hand-count").textContent = leaf.hand + " lines where the hand changes";
        document.getElementById("dip-count").textContent = leaf.dips + " on this leaf";
        document.getElementById("meta-section").textContent = leaf.section_name;
        document.getElementById("meta-stock").textContent = leaf.stock_label;
        document.getElementById("meta-side").textContent = leaf.side_label;
        document.getElementById("meta-lines").textContent = String(leaf.lines);
        document.getElementById("meta-condition").textContent = leaf.condition_label;
        document.getElementById("hand-note").textContent = leaf.hand_note;
        var readLink = document.getElementById("read-leaf");
        readLink.href = "/reader#sec-" + leaf.sec;

        ["dmg", "conf", "hand", "dips"].forEach(function (key) {
          var btn = document.getElementById("ly-" + key);
          var on = state.layers[key];
          btn.classList.toggle("on", on);
          btn.setAttribute("aria-pressed", on ? "true" : "false");
        });

        var list = document.getElementById("transcription");
        list.innerHTML = leaf.transcription.map(function (line) {
          return "<li><span class=\"n\">" + line.n + "</span><span class=\"line\" style=\"" + esc(line.style) + "\">" + esc(line.text) + "</span><span class=\"pct\" style=\"color:" + esc(line.col) + "\">" + esc(line.pct) + "</span></li>";
        }).join("");

        var strip = document.getElementById("filmstrip");
        var prev = 0;
        var bits = [];
        data.folios.forEach(function (item) {
          if (item.sec !== prev) {
            prev = item.sec;
            bits.push('<span class="film-gap" aria-hidden="true">' + esc(item.roman) + "</span>");
          }
          var dot = item.cond ? "#E0644B" : (item.sec === 7 ? "#8FB3D1" : "transparent");
          var on = item.id === leaf.id ? " ft on" : " ft";
          bits.push('<button class="' + on.trim() + '" type="button" data-folio="' + esc(item.id) + '" aria-label="Folio ' + esc(item.label) + '"' + (item.id === leaf.id ? ' aria-current="page"' : "") + '><img src="' + esc(item.thumb) + '" alt=""><span>' + esc(item.label) + ' <i class="dot" style="background:' + dot + '"></i></span></button>');
        });
        strip.innerHTML = bits.join("");
        var currentBtn = strip.querySelector(".ft.on");
        if (currentBtn) {
          strip.scrollLeft = currentBtn.offsetLeft - strip.clientWidth / 2 + currentBtn.clientWidth / 2;
        }
        applyTransform();
        var url = new URL(window.location.href);
        url.searchParams.set("folio", leaf.id);
        history.replaceState(null, "", url);
      }

      function go(id, reset) {
        if (!folio(id)) return;
        state.id = id;
        if (reset) {
          state.zoom = 1;
          state.panX = 0;
          state.panY = 0;
        }
        render();
      }

      document.getElementById("prev-folio").addEventListener("click", function () {
        var leaf = folio(state.id);
        var idx = data.folios.indexOf(leaf);
        if (idx > 0) go(data.folios[idx - 1].id, true);
      });
      document.getElementById("next-folio").addEventListener("click", function () {
        var leaf = folio(state.id);
        var idx = data.folios.indexOf(leaf);
        if (idx < data.folios.length - 1) go(data.folios[idx + 1].id, true);
      });
      document.getElementById("mode-leaf").addEventListener("click", function () {
        state.mode = "leaf";
        state.zoom = 1;
        state.panX = 0;
        state.panY = 0;
        render();
      });
      document.getElementById("mode-opening").addEventListener("click", function () {
        state.mode = "opening";
        state.zoom = 1;
        state.panX = 0;
        state.panY = 0;
        render();
      });
      document.getElementById("mode-weathered").addEventListener("click", function () {
        state.surface = "weathered";
        render();
      });
      document.getElementById("mode-clean").addEventListener("click", function () {
        state.surface = "clean";
        render();
      });
      document.getElementById("hide-panel").addEventListener("click", function () {
        app.classList.add("panel-hidden");
      });
      document.getElementById("show-panel").addEventListener("click", function () {
        app.classList.remove("panel-hidden");
      });
      document.getElementById("zoom-in").addEventListener("click", function () { setZoom(state.zoom * 1.25); });
      document.getElementById("zoom-out").addEventListener("click", function () { setZoom(state.zoom / 1.25); });
      document.getElementById("zoom-fit").addEventListener("click", function () {
        state.zoom = 1;
        state.panX = 0;
        state.panY = 0;
        applyTransform();
      });
      ["dmg", "conf", "hand", "dips"].forEach(function (key) {
        document.getElementById("ly-" + key).addEventListener("click", function () {
          state.layers[key] = !state.layers[key];
          render();
        });
      });
      document.getElementById("tab-apparatus").addEventListener("click", function () { setTab("apparatus"); });
      document.getElementById("tab-transcription").addEventListener("click", function () { setTab("transcription"); });
      document.getElementById("filmstrip").addEventListener("click", function (event) {
        var btn = event.target.closest("[data-folio]");
        if (btn) go(btn.getAttribute("data-folio"), true);
      });

      function setTab(tab) {
        state.tab = tab;
        var apparatus = document.getElementById("panel-apparatus");
        var transcription = document.getElementById("panel-transcription");
        apparatus.hidden = tab !== "apparatus";
        transcription.hidden = tab !== "transcription";
        document.getElementById("tab-apparatus").classList.toggle("on", tab === "apparatus");
        document.getElementById("tab-transcription").classList.toggle("on", tab === "transcription");
        document.getElementById("tab-apparatus").setAttribute("aria-selected", tab === "apparatus" ? "true" : "false");
        document.getElementById("tab-transcription").setAttribute("aria-selected", tab === "transcription" ? "true" : "false");
      }

      stage.addEventListener("pointerdown", function (event) {
        if (event.target.closest("button, a")) return;
        drag = { x: event.clientX, y: event.clientY, px: state.panX, py: state.panY };
        state.dragging = true;
        stage.classList.add("drag");
        stage.setPointerCapture(event.pointerId);
      });
      stage.addEventListener("pointermove", function (event) {
        if (!drag) return;
        state.panX = drag.px + (event.clientX - drag.x);
        state.panY = drag.py + (event.clientY - drag.y);
        applyTransform();
      });
      function endDrag() {
        if (!drag) return;
        drag = null;
        state.dragging = false;
        stage.classList.remove("drag");
        applyTransform();
      }
      stage.addEventListener("pointerup", endDrag);
      stage.addEventListener("pointercancel", endDrag);
      stage.addEventListener("wheel", function (event) {
        event.preventDefault();
        setZoom(state.zoom * (event.deltaY < 0 ? 1.1 : 1 / 1.1));
      }, { passive: false });
      window.addEventListener("keydown", function (event) {
        if (event.target.closest("input, textarea")) return;
        if (event.key === "ArrowLeft") document.getElementById("prev-folio").click();
        if (event.key === "ArrowRight") document.getElementById("next-folio").click();
      });

      setTab("apparatus");
      render();
    }
  }

  initAccent();
  initMenus();
  initReader();
  initFolios();
  initColophon();
  initViewer();
})();
