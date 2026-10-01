/**
 * Django Admin Custom JS for Summernote Theme Controls
 * Injects a Dark / Light theme control bar above rich text content boxes in Django Admin.
 */
(function () {
    'use strict';

    var STORAGE_KEY = 'admin_summernote_theme';

    function getSavedTheme() {
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            if (saved === 'light' || saved === 'dark') {
                return saved;
            }
        } catch (e) {}
        return 'dark'; // Default to dark mode
    }

    function saveTheme(theme) {
        try {
            localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) {}
    }

    function syncThemeToAllIframes(theme) {
        var isDark = (theme === 'dark');
        var iframes = document.querySelectorAll('.django-summernote-widgets iframe, .summernote-div iframe, iframe[id$="_iframe"]');
        
        iframes.forEach(function (iframe) {
            try {
                if (iframe.contentWindow) {
                    iframe.contentWindow.postMessage({
                        type: 'SET_SUMMERNOTE_THEME',
                        theme: theme
                    }, '*');
                }
            } catch (e) {}

            try {
                if (iframe.contentDocument && iframe.contentDocument.body) {
                    var doc = iframe.contentDocument;
                    if (isDark) {
                        doc.body.classList.add('editor-dark-mode');
                        doc.body.classList.remove('editor-light-mode');
                        var editors = doc.querySelectorAll('.note-editor, .note-editable');
                        editors.forEach(function (el) {
                            el.classList.add('editor-dark-mode');
                            el.classList.remove('editor-light-mode');
                        });
                    } else {
                        doc.body.classList.add('editor-light-mode');
                        doc.body.classList.remove('editor-dark-mode');
                        var editors = doc.querySelectorAll('.note-editor, .note-editable');
                        editors.forEach(function (el) {
                            el.classList.add('editor-light-mode');
                            el.classList.remove('editor-dark-mode');
                        });
                    }
                }
            } catch (e) {}
        });
    }

    function updateAdminBarButtons(theme) {
        var isDark = (theme === 'dark');
        var bars = document.querySelectorAll('.summernote-theme-bar');
        bars.forEach(function (bar) {
            var darkBtn = bar.querySelector('.btn-theme-dark');
            var lightBtn = bar.querySelector('.btn-theme-light');
            if (darkBtn && lightBtn) {
                if (isDark) {
                    darkBtn.classList.add('active');
                    lightBtn.classList.remove('active');
                } else {
                    lightBtn.classList.add('active');
                    darkBtn.classList.remove('active');
                }
            }
        });
    }

    function injectThemeControls() {
        var summernoteContainers = document.querySelectorAll(
            '.form-row.field-description, .form-row.field-content, .form-row.field-bio, .django-summernote-widgets'
        );

        var currentTheme = getSavedTheme();

        summernoteContainers.forEach(function (container) {
            // Avoid duplicate bars
            if (container.querySelector('.summernote-theme-bar')) {
                return;
            }

            var widgetDiv = container.querySelector('.django-summernote-widgets, .summernote-div, iframe');
            if (!widgetDiv) {
                return;
            }

            var bar = document.createElement('div');
            bar.className = 'summernote-theme-bar';
            bar.innerHTML = [
                '<div class="theme-bar-content">',
                '  <span class="theme-bar-label"><strong>Content Box Theme:</strong></span>',
                '  <div class="theme-btn-group">',
                '    <button type="button" class="btn-theme-admin btn-theme-dark' + (currentTheme === 'dark' ? ' active' : '') + '" data-theme="dark">',
                '      <span class="theme-icon">🌙</span> Dark Box (Matches Site)',
                '    </button>',
                '    <button type="button" class="btn-theme-admin btn-theme-light' + (currentTheme === 'light' ? ' active' : '') + '" data-theme="light">',
                '      <span class="theme-icon">☀️</span> Light Box',
                '    </button>',
                '  </div>',
                '  <span class="theme-bar-hint">Preview white/light text and media against the dark site theme</span>',
                '</div>'
            ].join('');

            // Click handling for buttons
            bar.querySelectorAll('.btn-theme-admin').forEach(function (btn) {
                btn.addEventListener('click', function (e) {
                    e.preventDefault();
                    var selectedTheme = this.getAttribute('data-theme');
                    saveTheme(selectedTheme);
                    updateAdminBarButtons(selectedTheme);
                    syncThemeToAllIframes(selectedTheme);
                });
            });

            // Insert before widget
            if (widgetDiv.parentNode) {
                widgetDiv.parentNode.insertBefore(bar, widgetDiv);
            }
        });

        // Also bind load events to any iframes to sync theme on load
        var iframes = document.querySelectorAll('.django-summernote-widgets iframe, .summernote-div iframe, iframe[id$="_iframe"]');
        iframes.forEach(function (iframe) {
            iframe.addEventListener('load', function () {
                setTimeout(function () {
                    syncThemeToAllIframes(getSavedTheme());
                }, 100);
            });
        });

        syncThemeToAllIframes(currentTheme);
    }

    // Listen for theme change messages from iframes
    window.addEventListener('message', function (event) {
        if (!event.data) return;
        if (event.data.type === 'SUMMERNOTE_THEME_CHANGED') {
            var theme = event.data.theme;
            if (theme === 'dark' || theme === 'light') {
                saveTheme(theme);
                updateAdminBarButtons(theme);
                syncThemeToAllIframes(theme);
            }
        }
    });

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectThemeControls);
    } else {
        injectThemeControls();
    }

    // Repeat after a short delay to catch dynamic form/inline elements
    setTimeout(injectThemeControls, 500);
    setTimeout(injectThemeControls, 1500);
})();
