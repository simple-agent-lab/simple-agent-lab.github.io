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
})();
