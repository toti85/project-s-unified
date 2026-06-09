/**
 * SHAYANWATERS.COM — Main JavaScript
 * Navigation, Dark Mode, Scroll, Mobile Menu, Cookie Banner
 * Date: 2026-06-03
 * Pure ES6+ — No jQuery
 */

(function () {
  'use strict';

  // ============================================================
  // 1. DOM READY
  // ============================================================

  document.addEventListener('DOMContentLoaded', function () {
    initHeader();
    initMobileMenu();
    initDarkMode();
    initCookieBanner();
    initLazyImages();
    initSmoothScroll();
  });

  // ============================================================
  // 2. HEADER — Transparent → Solid on Scroll
  // ============================================================

  function initHeader() {
    const header = document.querySelector('.header');
    if (!header) return;

    let ticking = false;

    window.addEventListener('scroll', function () {
      if (!ticking) {
        window.requestAnimationFrame(function () {
          if (window.scrollY > 50) {
            header.classList.add('scrolled');
          } else {
            header.classList.remove('scrolled');
          }
          ticking = false;
        });
        ticking = true;
      }
    });
  }

  // ============================================================
  // 3. MOBILE MENU
  // ============================================================

  function initMobileMenu() {
    const hamburger = document.querySelector('.hamburger');
    const mobileMenu = document.querySelector('.mobile-menu');
    const overlay = document.querySelector('.mobile-menu__overlay');
    if (!hamburger || !mobileMenu) return;

    function toggleMenu() {
      const isOpen = mobileMenu.classList.contains('open');
      hamburger.classList.toggle('active');
      mobileMenu.classList.toggle('open');
      if (overlay) overlay.classList.toggle('open');
      document.body.style.overflow = isOpen ? '' : 'hidden';
    }

    function closeMenu() {
      hamburger.classList.remove('active');
      mobileMenu.classList.remove('open');
      if (overlay) overlay.classList.remove('open');
      document.body.style.overflow = '';
    }

    hamburger.addEventListener('click', toggleMenu);
    if (overlay) overlay.addEventListener('click', closeMenu);

    // Close on link click
    const links = mobileMenu.querySelectorAll('.mobile-menu__link');
    links.forEach(function (link) {
      link.addEventListener('click', closeMenu);
    });

    // Close on Escape
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && mobileMenu.classList.contains('open')) {
        closeMenu();
      }
    });
  }

  // ============================================================
  // 4. DARK MODE
  // ============================================================

  function initDarkMode() {
    const toggle = document.querySelector('.theme-toggle');
    if (!toggle) return;

    // Check stored preference or system preference
    const stored = localStorage.getItem('theme');
    if (stored) {
      document.documentElement.setAttribute('data-theme', stored);
      updateToggleIcon(stored === 'dark');
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
      updateToggleIcon(true);
    }

    toggle.addEventListener('click', function () {
      const current = document.documentElement.getAttribute('data-theme');
      const isDark = current === 'dark';

      if (isDark) {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        updateToggleIcon(false);
      } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        updateToggleIcon(true);
      }
    });

    // Listen for system preference changes
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (e) {
        if (!localStorage.getItem('theme')) {
          const isDark = e.matches;
          document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
          updateToggleIcon(isDark);
        }
      });
    }
  }

  function updateToggleIcon(isDark) {
    const toggle = document.querySelector('.theme-toggle');
    if (!toggle) return;
    toggle.textContent = isDark ? '☀️' : '🌙';
    toggle.setAttribute('aria-label', isDark ? 'Váltás világos témára' : 'Váltás sötét témára');
  }

  // ============================================================
  // 5. COOKIE BANNER
  // ============================================================

  function initCookieBanner() {
    const banner = document.querySelector('.cookie-banner');
    const btn = document.querySelector('.cookie-banner__btn');
    if (!banner || !btn) return;

    // Check if user already accepted
    if (!localStorage.getItem('cookies-accepted')) {
      setTimeout(function () {
        banner.classList.add('visible');
      }, 1500);
    }

    btn.addEventListener('click', function () {
      localStorage.setItem('cookies-accepted', 'true');
      banner.classList.remove('visible');
    });
  }

  // ============================================================
  // 6. LAZY IMAGES — Mark as loaded when visible
  // ============================================================

  function initLazyImages() {
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('loaded');
            observer.unobserve(entry.target);
          }
        });
      }, { rootMargin: '200px' });

      lazyImages.forEach(function (img) {
        observer.observe(img);
      });
    } else {
      // Fallback: mark all as loaded
      lazyImages.forEach(function (img) {
        img.classList.add('loaded');
      });
    }
  }

  // ============================================================
  // 7. SMOOTH SCROLL for anchor links
  // ============================================================

  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
      anchor.addEventListener('click', function (e) {
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;

        const target = document.querySelector(targetId);
        if (target) {
          e.preventDefault();
          const headerHeight = document.querySelector('.header')?.offsetHeight || 0;
          const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - headerHeight;

          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
        }
      });
    });
  }

  // ============================================================
  // 8. AOS INITIALIZATION (if AOS library is loaded)
  // ============================================================

  if (typeof AOS !== 'undefined') {
    window.addEventListener('load', function () {
      AOS.init({
        duration: 600,
        easing: 'ease-out-cubic',
        once: true,
        offset: 80,
        disable: function () {
          // Disable on mobile for performance
          return window.innerWidth < 768;
        }
      });
    });
  }
})();