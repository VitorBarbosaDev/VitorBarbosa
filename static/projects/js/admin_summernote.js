/**
 * Summernote Editor Admin Plugin - Dark / Light Content Box Toggle
 * Matches the portfolio site dark theme (#121212) with instant toggle & persistence.
 */
(function ($) {
    'use strict';

    if (!$) {
        if (typeof window.jQuery !== 'undefined') {
            $ = window.jQuery;
        } else if (typeof window.$ !== 'undefined') {
            $ = window.$;
        } else {
            return;
        }
    }

    var STORAGE_KEY = 'admin_summernote_theme';
    var currentThemeState = null;

    function getSavedTheme() {
        try {
            var saved = localStorage.getItem(STORAGE_KEY);
            if (saved === 'light' || saved === 'dark') {
                return saved;
            }
        } catch (e) {
            // LocalStorage access restricted or unavailable
        }
        return 'dark'; // Default to dark mode to match site
    }

    function saveTheme(theme) {
        try {
            localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) {}
    }

    function applyThemeToDocument(isDark, $editor, notifyParent) {
        var newTheme = isDark ? 'dark' : 'light';
        var $body = $('body');

        // Apply theme classes idempotently
        if (isDark) {
            $body.addClass('editor-dark-mode').removeClass('editor-light-mode');
            if ($editor && $editor.length) {
                $editor.addClass('editor-dark-mode').removeClass('editor-light-mode');
                $editor.find('.note-editable').addClass('editor-dark-mode').removeClass('editor-light-mode');
            } else {
                $('.note-editor, .note-editable').addClass('editor-dark-mode').removeClass('editor-light-mode');
            }
        } else {
            $body.addClass('editor-light-mode').removeClass('editor-dark-mode');
            if ($editor && $editor.length) {
                $editor.addClass('editor-light-mode').removeClass('editor-dark-mode');
                $editor.find('.note-editable').addClass('editor-light-mode').removeClass('editor-dark-mode');
            } else {
                $('.note-editor, .note-editable').addClass('editor-light-mode').removeClass('editor-dark-mode');
            }
        }

        // Update all toggle buttons in this iframe
        var $btn = $('.btn-theme-toggle');
        if ($btn.length) {
            if (isDark) {
                $btn.addClass('btn-dark-active').removeClass('btn-light-active');
                $btn.html('<span class="theme-toggle-icon">☀️</span> <span class="theme-toggle-text">Light Box</span>');
                $btn.attr('title', 'Switch to Light Content Box');
            } else {
                $btn.addClass('btn-light-active').removeClass('btn-dark-active');
                $btn.html('<span class="theme-toggle-icon">🌙</span> <span class="theme-toggle-text">Dark Box</span>');
                $btn.attr('title', 'Switch to Dark Content Box (Matches Dark Website)');
            }
        }

        currentThemeState = newTheme;

        // ONLY notify parent if explicitly requested (e.g. user clicked inside this iframe)
        // Never notify parent when reacting to a message from parent to prevent infinite loops!
        if (notifyParent && window.parent && window.parent !== window) {
            try {
                window.parent.postMessage({
                    type: 'SUMMERNOTE_THEME_CHANGED',
                    theme: newTheme
                }, '*');
            } catch (e) {}
        }
    }

    // Register plugin with Summernote
    if ($.summernote) {
        $.extend($.summernote.plugins, {
            'themeToggle': function (context) {
                var ui = $.summernote.ui;
                var $editor = context.layoutInfo.editor;

                // Create custom button for toolbar
                context.memo('button.themeToggle', function () {
                    var currentTheme = getSavedTheme();
                    var isDark = (currentTheme === 'dark');

                    var button = ui.button({
                        contents: isDark
                            ? '<span class="theme-toggle-icon">☀️</span> <span class="theme-toggle-text">Light Box</span>'
                            : '<span class="theme-toggle-icon">🌙</span> <span class="theme-toggle-text">Dark Box</span>',
                        tooltip: isDark
                            ? 'Switch to Light Content Box'
                            : 'Switch to Dark Content Box (Matches Dark Website)',
                        className: 'btn-theme-toggle ' + (isDark ? 'btn-dark-active' : 'btn-light-active'),
                        click: function (e) {
                            if (e && e.preventDefault) e.preventDefault();
                            var willBeDark = !$('body').hasClass('editor-dark-mode');
                            saveTheme(willBeDark ? 'dark' : 'light');
                            applyThemeToDocument(willBeDark, $editor, true);
                        }
                    });
                    return button.render();
                });

                this.initialize = function () {
                    var theme = getSavedTheme();
                    applyThemeToDocument(theme === 'dark', $editor, false);
                };
            }
        });
    }

    // Apply saved theme immediately on DOM ready
    $(document).ready(function () {
        var theme = getSavedTheme();
        applyThemeToDocument(theme === 'dark', $('.note-editor'), false);
    });

    // Listen for messages from parent window
    window.addEventListener('message', function (event) {
        if (!event.data) return;
        if (event.data.type === 'SET_SUMMERNOTE_THEME') {
            var theme = event.data.theme;
            if (theme === 'dark' || theme === 'light') {
                if (theme !== currentThemeState) {
                    saveTheme(theme);
                    applyThemeToDocument(theme === 'dark', $('.note-editor'), false);
                }
            }
        }
    });

    // Listen for storage changes across tabs
    window.addEventListener('storage', function (event) {
        if (event.key === STORAGE_KEY) {
            var theme = event.newValue || 'dark';
            if (theme !== currentThemeState) {
                applyThemeToDocument(theme === 'dark', $('.note-editor'), false);
            }
        }
    });

})(window.jQuery || window.$);
