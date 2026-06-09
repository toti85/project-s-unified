/* ============================================
   SHAYANWATERS BOLD VARIANT — main.js
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

    /* ---- AOS INIT ---- */
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-out-cubic',
            once: true,
            offset: 80
        });
    }

    /* ---- HERO LETTER SPLIT ---- */
    const heroTitle = document.getElementById('hero-title');
    if (heroTitle) {
        const text = heroTitle.textContent;
        heroTitle.innerHTML = '';
        text.split('').forEach((char, i) => {
            const span = document.createElement('span');
            span.className = 'letter';
            span.textContent = char;
            span.style.animationDelay = `${0.2 + i * 0.12}s`;
            heroTitle.appendChild(span);
        });
    }

    /* ---- HEADER SCROLL ---- */
    const header = document.querySelector('.header');
    let lastScroll = 0;

    const handleHeaderScroll = () => {
        const currentScroll = window.pageYOffset;
        if (currentScroll > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        lastScroll = currentScroll;
    };

    window.addEventListener('scroll', handleHeaderScroll, { passive: true });

    /* ---- HAMBURGER MENU ---- */
    const hamburger = document.querySelector('.hamburger');
    const mobileMenu = document.querySelector('.mobile-menu');
    const mobileOverlay = document.querySelector('.mobile-menu__overlay');
    const mobileLinks = document.querySelectorAll('.mobile-menu__link');

    const toggleMobileMenu = () => {
        const isActive = mobileMenu.classList.contains('active');
        hamburger.setAttribute('aria-expanded', !isActive);
        hamburger.classList.toggle('active');
        mobileMenu.classList.toggle('active');
        mobileOverlay.classList.toggle('active');
        document.body.style.overflow = isActive ? '' : 'hidden';
    };

    const closeMobileMenu = () => {
        hamburger.setAttribute('aria-expanded', 'false');
        hamburger.classList.remove('active');
        mobileMenu.classList.remove('active');
        mobileOverlay.classList.remove('active');
        document.body.style.overflow = '';
    };

    if (hamburger) hamburger.addEventListener('click', toggleMobileMenu);
    if (mobileOverlay) mobileOverlay.addEventListener('click', closeMobileMenu);
    mobileLinks.forEach(link => link.addEventListener('click', closeMobileMenu));

    /* ---- CURSOR GLOW (desktop only) ---- */
    if (window.matchMedia('(pointer: fine)').matches) {
        const glow = document.createElement('div');
        glow.className = 'cursor-glow';
        document.body.appendChild(glow);

        let mouseX = 0, mouseY = 0;
        let glowX = 0, glowY = 0;

        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        const animateGlow = () => {
            glowX += (mouseX - glowX) * 0.08;
            glowY += (mouseY - glowY) * 0.08;
            glow.style.left = glowX + 'px';
            glow.style.top = glowY + 'px';
            requestAnimationFrame(animateGlow);
        };
        animateGlow();
    }

    /* ---- VIDEO FALLBACK (mobile data saver) ---- */
    const heroVideo = document.querySelector('.hero__video');
    const heroFallback = document.querySelector('.hero__fallback');

    if (heroVideo && heroFallback) {
        const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
        const saveData = navigator.saveData;

        if (isMobile || saveData) {
            heroVideo.style.display = 'none';
            heroFallback.style.display = 'block';
        }

        // Try to play video, fallback on error
        heroVideo.addEventListener('error', () => {
            heroVideo.style.display = 'none';
            heroFallback.style.display = 'block';
        });
    }

    /* ---- COOKIE BANNER ---- */
    const cookieBanner = document.querySelector('.cookie-banner');
    const cookieBtn = document.querySelector('.cookie-banner__btn');

    if (cookieBanner && cookieBtn) {
        const cookieAccepted = localStorage.getItem('cookieAccepted');
        if (!cookieAccepted) {
            setTimeout(() => cookieBanner.classList.add('show'), 2000);
        }

        cookieBtn.addEventListener('click', () => {
            cookieBanner.classList.remove('show');
            localStorage.setItem('cookieAccepted', 'true');
        });
    }

    /* ---- THEME TOGGLE (dark/light) ---- */
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
        const savedTheme = localStorage.getItem('theme');
        const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        if (savedTheme === 'light' || !systemDark) {
            // Bold variant is dark-first; light mode is a radical shift
            document.body.classList.add('light-mode');
            themeToggle.textContent = '☀️';
        }

        themeToggle.addEventListener('click', () => {
            const isLight = document.body.classList.toggle('light-mode');
            localStorage.setItem('theme', isLight ? 'light' : 'dark');
            themeToggle.textContent = isLight ? '☀️' : '🌙';
        });
    }

    /* ---- SCROLL REVEAL (custom, lightweight) ---- */
    const revealElements = document.querySelectorAll('.reveal');
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    revealElements.forEach(el => revealObserver.observe(el));

    /* ---- STORY PARALLAX ---- */
    const storyLayers = document.querySelectorAll('.story__layer--bg');
    const handleParallax = () => {
        const scrollY = window.pageYOffset;
        storyLayers.forEach(layer => {
            const parent = layer.parentElement;
            const parentTop = parent.offsetTop;
            const offset = (scrollY - parentTop) * 0.15;
            layer.style.transform = `translateY(${offset}px)`;
        });
    };

    window.addEventListener('scroll', handleParallax, { passive: true });

    /* ---- SMOOTH SCROLL (internal anchors) ---- */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', (e) => {
            const targetId = anchor.getAttribute('href');
            if (targetId === '#') return;
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    /* ---- LAZY IMAGES (native loading="lazy" fallback) ---- */
    if ('loading' in HTMLImageElement.prototype) {
        // Native lazy loading supported
    } else {
        // Fallback: IntersectionObserver for lazy images
        const lazyImages = document.querySelectorAll('img[loading="lazy"]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                    }
                    imageObserver.unobserve(img);
                }
            });
        });
        lazyImages.forEach(img => imageObserver.observe(img));
    }

}); // end DOMContentLoaded