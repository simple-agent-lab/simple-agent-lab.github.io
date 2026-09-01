(function () {
  "use strict";

  var root = document.documentElement;
  var languageToggle = document.querySelector(".language-toggle");
  var themeToggle = document.querySelector(".theme-toggle");
  var themeActionEnglish = document.querySelector(".theme-action-en");
  var themeActionChinese = document.querySelector(".theme-action-zh");
  var systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

  function browserLanguage() {
    var languages = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || "en"];
    return languages.some(function (language) {
      return language.toLowerCase().startsWith("zh");
    }) ? "zh" : "en";
  }

  function setLanguage(language, remember) {
    var isChinese = language === "zh";
    root.dataset.lang = isChinese ? "zh" : "en";
    root.lang = isChinese ? "zh-CN" : "en";
    languageToggle.textContent = isChinese ? "EN" : "中文";
    languageToggle.setAttribute("aria-label", isChinese ? "Switch to English" : "切换为中文");

    if (remember) {
      try {
        localStorage.setItem("simple-agent-lab-language-choice", isChinese ? "zh" : "en");
      } catch (error) {}
    }
  }

  function setTheme(theme, remember) {
    var isDark = theme === "dark";
    root.dataset.theme = isDark ? "dark" : "light";
    root.style.colorScheme = isDark ? "dark" : "light";
    themeActionEnglish.textContent = isDark ? "Light" : "Dark";
    themeActionChinese.textContent = isDark ? "浅色" : "深色";
    themeToggle.setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
    document.querySelector('meta[name="theme-color"]').setAttribute(
      "content",
      isDark ? "#111513" : "#ffffff"
    );

    if (remember) {
      try {
        localStorage.setItem("simple-agent-lab-theme", isDark ? "dark" : "light");
      } catch (error) {}
    }
  }

  languageToggle.addEventListener("click", function () {
    setLanguage(root.dataset.lang === "zh" ? "en" : "zh", true);
  });

  themeToggle.addEventListener("click", function () {
    setTheme(root.dataset.theme === "dark" ? "light" : "dark", true);
  });

  systemTheme.addEventListener("change", function (event) {
    try {
      if (localStorage.getItem("simple-agent-lab-theme")) return;
    } catch (error) {}
    setTheme(event.matches ? "dark" : "light", false);
  });

  window.addEventListener("languagechange", function () {
    try {
      if (localStorage.getItem("simple-agent-lab-language-choice")) return;
    } catch (error) {}
    setLanguage(browserLanguage(), false);
  });

  setLanguage(root.dataset.lang === "zh" ? "zh" : "en", false);
  setTheme(root.dataset.theme === "dark" ? "dark" : "light", false);

  var zoomableImages = document.querySelectorAll(
    ".project-page figure img, .showcase-grid figure img"
  );
  var lightbox = null;
  var lightboxTrigger = null;

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.remove();
    lightbox = null;
    document.body.style.overflow = "";
    if (lightboxTrigger) lightboxTrigger.focus();
    lightboxTrigger = null;
  }

  function openLightbox(image) {
    closeLightbox();
    lightboxTrigger = image;
    lightbox = document.createElement("div");
    lightbox.className = "lightbox";
    lightbox.setAttribute("role", "dialog");
    lightbox.setAttribute("aria-modal", "true");
    lightbox.setAttribute("aria-label", image.alt || "Enlarged image");
    lightbox.tabIndex = -1;

    var enlarged = document.createElement("img");
    enlarged.src = image.currentSrc || image.src;
    enlarged.alt = image.alt || "";
    lightbox.appendChild(enlarged);

    lightbox.addEventListener("click", closeLightbox);
    document.body.appendChild(lightbox);
    document.body.style.overflow = "hidden";
    lightbox.focus();
  }

  Array.prototype.forEach.call(zoomableImages, function (image) {
    image.tabIndex = 0;
    image.setAttribute("role", "button");
    image.addEventListener("click", function () {
      openLightbox(image);
    });
    image.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openLightbox(image);
      }
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeLightbox();
  });
})();
