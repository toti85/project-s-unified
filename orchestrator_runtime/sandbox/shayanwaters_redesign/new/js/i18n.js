/**
 * SHAYANWATERS.COM — i18n Module
 * Structured for future multilingual support
 * Date: 2026-06-03
 */
(function () {
  'use strict';
  window.i18n = {
    currentLang: 'uk',
    fallbackLang: 'uk',
    translations: {},
    init: function () {
      this.detectLanguage();
      this.translate();
    },
    detectLanguage: function () {
      var urlParams = new URLSearchParams(window.location.search);
      var urlLang = urlParams.get('lang');
      if (urlLang && this.translations[urlLang]) { this.currentLang = urlLang; return; }
      var stored = localStorage.getItem('lang');
      if (stored && this.translations[stored]) { this.currentLang = stored; return; }
      var browserLang = navigator.language ? navigator.language.substring(0, 2) : null;
      if (browserLang && this.translations[browserLang]) { this.currentLang = browserLang; return; }
      this.currentLang = this.fallbackLang;
    },
    setLanguage: function (lang) {
      if (!this.translations[lang]) return;
      this.currentLang = lang;
      localStorage.setItem('lang', lang);
      document.documentElement.setAttribute('lang', lang);
      this.translate();
    },
    translate: function () {
      var t = this.translations[this.currentLang];
      if (!t) return;
      var self = this;
      document.querySelectorAll('[data-i18n]').forEach(function (el) {
        var key = el.getAttribute('data-i18n');
        var value = self.getKey(t, key);
        if (value) el.textContent = value;
      });
    },
    getKey: function (obj, key) {
      return key.split('.').reduce(function (o, k) { return o ? o[k] : undefined; }, obj);
    },
    loadTranslations: async function () {
      // Future: fetch(`js/translations/${this.currentLang}.json`)
    }
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { window.i18n.init(); });
  } else { window.i18n.init(); }
})();