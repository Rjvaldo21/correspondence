(() => {
  /* ========= Locale-aware now() ========= */
  const htmlLang = (
    document.documentElement.getAttribute("lang") || ""
  ).toLowerCase();
  const LANG = htmlLang.startsWith("tet")
    ? "tet"
    : htmlLang.startsWith("pt")
    ? "pt-PT"
    : "id-ID"; // default dev

  // Tetun formatter (hari & fulan populer)
  const TET = {
    days: ["Domingu", "Segunda", "Tersa", "Kuarta", "Kinta", "Sesta", "Sabadu"],
    months: [
      "Janeiru",
      "Fevereiru",
      "Marsu",
      "Abríl",
      "Maiu",
      "Juñu",
      "Julhu",
      "Agostu",
      "Setembru",
      "Outubru",
      "Novembru",
      "Dezembru",
    ],
    fmt(d) {
      const dd = d.getDate().toString().padStart(2, "0");
      const mm = TET.months[d.getMonth()];
      const yyyy = d.getFullYear();
      const day = TET.days[d.getDay()];
      const hh = d.getHours().toString().padStart(2, "0");
      const min = d.getMinutes().toString().padStart(2, "0");
      return `${day}, ${dd} ${mm} ${yyyy}, ${hh}:${min}`;
    },
  };

  function formatNow() {
    try {
      const now = new Date();
      if (LANG === "tet") return TET.fmt(now);
      const optDate = {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric",
      };
      const optTime = { hour: "2-digit", minute: "2-digit" };
      return `${now.toLocaleDateString(
        LANG,
        optDate,
      )}, ${now.toLocaleTimeString(LANG, optTime)}`;
    } catch {
      return new Date().toISOString();
    }
  }

  function renderNow() {
    const el = document.getElementById("of-now");
    if (el) el.textContent = formatNow();
  }

  // Render pertama + sinkron ke pergantian menit
  renderNow();
  const msToNextMinute = 60000 - (Date.now() % 60000);
  setTimeout(() => {
    renderNow();
    setInterval(renderNow, 60000);
  }, msToNextMinute);

  /* ========= Bootstrap tooltips (opsional) ========= */
  if (window.bootstrap) {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      try {
        new bootstrap.Tooltip(el);
      } catch {}
    });
  }

  /* ========= DataTables auto-init ========= */
  document.addEventListener("DOMContentLoaded", () => {
    if (typeof window.$ === "undefined" || !$.fn || !$.fn.dataTable) return;

    const tetLang = {
      emptyTable: "Seidauk iha dadus.",
      info: "Hatudu _START_ to'o _END_ husi _TOTAL_ rejistu",
      infoEmpty: "La iha rejistu",
      infoFiltered: "(filtra hosi _MAX_ rejistu hotu)",
      lengthMenu: "Hatudu _MENU_",
      loadingRecords: "Halo karga...",
      processing: "Prosesu...",
      search: "Buka:",
      zeroRecords: "La hetan rezultadu.",
      paginate: {
        first: "Primeiru",
        last: "Ikus",
        next: "Tuir-mai",
        previous: "Antes",
      },
    };

    $(".datatable-auto").each(function () {
      const $t = $(this);
      if ($t.data("dt-init")) return;
      $t.data("dt-init", true);

      const pageLength = parseInt($t.data("page-length"), 10) || 10;
      $t.DataTable({
        pageLength,
        lengthMenu: [10, 25, 50, 100],
        ordering: true,
        responsive: true,
        autoWidth: false,
        language: tetLang,
        dom:
          "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
          "t" +
          "<'row'<'col-sm-6'i><'col-sm-6'p>>",
      });
    });
  });

  console.debug("admin_surat.js loaded (LANG =", LANG, ")");
})();

/* =========================
   FLAG halaman & kontrol brand header
   ========================= */
(function () {
  // 1) Tandai tipe halaman
  const pathClean = location.pathname.replace(/\/+$/, "");
  const isAdminPath = /^\/admin(\/|$)/.test(location.pathname);
  const hasSidebar = !!document.querySelector("aside.main-sidebar");

  document.body.classList.toggle("of-admin-root", pathClean === "/admin");
  document.body.classList.toggle("of-jazzmin", hasSidebar || isAdminPath);
  document.body.classList.toggle("of-pimpinan", !isAdminPath && !hasSidebar);

  // 2) Tema soft hanya untuk admin
  if (hasSidebar || isAdminPath) {
    document.body.classList.add("of-soft");
  } else {
    document.body.classList.remove("of-soft");
  }

  // 3) Util: sembunyikan brand di admin, tampilkan di pimpinan
  const BRAND_SELECTORS = [
    ".main-header .navbar .navbar-brand",
    ".main-header .navbar a.navbar-brand",
    ".main-header .navbar .brand-link",
    ".main-header .navbar .brand-text",
    ".main-header .navbar img.brand-image",
    ".main-header .navbar .brand-logo",
    '.main-header .navbar .navbar-nav > .nav-item > .nav-link[href$="/admin"]',
    '.main-header .navbar .navbar-nav > .nav-item > .nav-link[href$="/admin/"]',
  ].join(",");

  function hideAdminBrand() {
    if (!document.body.classList.contains("of-jazzmin")) return;

    // Total hide for brand elements
    document.querySelectorAll(BRAND_SELECTORS).forEach((el) => {
      el.style.setProperty("display", "none", "important");
      el.style.setProperty("background", "none", "important");
      el.style.setProperty("padding", "0", "important");
      el.style.setProperty("margin", "0", "important");
      el.style.setProperty("width", "0", "important");
      el.style.setProperty("font-size", "0", "important");
      el.style.setProperty("color", "transparent", "important");
    });

    // Show hamburger only on mobile (≤768px)
    const isMobile = window.innerWidth <= 768;
    document
      .querySelectorAll(
        '.main-header .navbar-nav .nav-link[data-widget="pushmenu"], .main-header .navbar-nav .nav-link .fa-bars',
      )
      .forEach((el) => {
        if (isMobile) {
          el.style.setProperty("display", "inline-flex", "important");
          el.style.setProperty("justify-content", "flex-start", "important");
          el.style.setProperty("align-items", "center", "important"); // optional, keeps it vertically aligned
        } else {
          el.style.setProperty("display", "none", "important");
          el.style.removeProperty("justify-content");
          el.style.removeProperty("align-items");
        }
      });
  }

  function showPimpinanBrand() {
    if (!document.body.classList.contains("of-pimpinan")) return;

    document.querySelectorAll(BRAND_SELECTORS).forEach((el) => {
      el.style.removeProperty("display");
      el.style.removeProperty("width");
      el.style.removeProperty("font-size");
      el.style.removeProperty("color");
      el.style.setProperty("pointer-events", "none", "important");
      el.style.setProperty(
        "background",
        'url("/static/core/img/tic-timor.svg") left center / 24px 24px no-repeat',
        "important",
      );
      el.style.setProperty("padding-left", "32px", "important");
    });
  }

  function applyBrandPolicy() {
    if (document.body.classList.contains("of-jazzmin")) {
      hideAdminBrand();
    } else if (document.body.classList.contains("of-pimpinan")) {
      showPimpinanBrand();
    }
  }

  // Apply policy on load and resize (responsive)
  window.addEventListener("load", applyBrandPolicy);
  window.addEventListener("resize", applyBrandPolicy);

  document.addEventListener("DOMContentLoaded", applyBrandPolicy);
  // Observer: kalau header diubah/dire-render Jazzmin, terapkan lagi.
  const header = document.querySelector(".main-header");
  if (header) {
    const mo = new MutationObserver(applyBrandPolicy);
    mo.observe(header, { childList: true, subtree: true });
  }
})();
