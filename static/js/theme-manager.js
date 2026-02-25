(function () {
    const STORAGE_KEY = 'app-theme';
    const LEGACY_STORAGE_KEY = 'theme';

    function getRegistry() {
        const registry = window.__THEME_REGISTRY__;
        return Array.isArray(registry) ? registry : [];
    }

    function getDefaultTheme(registry) {
        const light = registry.find((item) => item.id === 'light');
        if (light) return light;
        if (registry.length > 0) return registry[0];
        return {
            id: 'light',
            name: '默认主题',
            mode: 'light',
            stylesheet: 'themes/light/theme.css',
        };
    }

    function findTheme(themeId, registry) {
        return registry.find((item) => item.id === themeId);
    }

    function safeGetStorage(key) {
        try {
            return window.localStorage.getItem(key);
        } catch (_) {
            return null;
        }
    }

    function safeSetStorage(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch (_) {
            // ignore storage failures in privacy mode
        }
    }

    function isDarkTheme(theme) {
        return (theme && theme.mode === 'dark') || (theme && theme.id === 'dark');
    }

    function getStylesheetHref(theme) {
        const staticBaseRaw = window.__STATIC_BASE_URL__ || '/static/';
        const staticBase = staticBaseRaw.endsWith('/') ? staticBaseRaw : `${staticBaseRaw}/`;
        const stylesheet = (theme && theme.stylesheet) || 'themes/light/theme.css';
        return `${staticBase}${stylesheet}`;
    }

    function ensureThemeStylesheetLink(href) {
        let link = document.getElementById('app-theme-style');
        if (!link) {
            link = document.createElement('link');
            link.id = 'app-theme-style';
            link.rel = 'stylesheet';
            document.head.appendChild(link);
        }
        if (link.getAttribute('href') !== href) {
            link.setAttribute('href', href);
        }
        return link;
    }

    function resolveTheme(themeId) {
        const registry = getRegistry();
        const fallback = getDefaultTheme(registry);
        const resolved = findTheme(themeId, registry) || fallback;
        return resolved;
    }

    function applyTheme(themeId, options = {}) {
        const { persist = true, emit = true } = options;
        const theme = resolveTheme(themeId);
        const html = document.documentElement;
        const dark = isDarkTheme(theme);

        html.setAttribute('data-theme', theme.id);
        html.classList.toggle('dark', dark);

        const href = getStylesheetHref(theme);
        ensureThemeStylesheetLink(href);

        if (persist) {
            safeSetStorage(STORAGE_KEY, theme.id);
            safeSetStorage(LEGACY_STORAGE_KEY, dark ? 'dark' : 'light');
        }

        if (emit) {
            window.dispatchEvent(new CustomEvent('app:theme-change', {
                detail: {
                    themeId: theme.id,
                    mode: theme.mode,
                    isDark: dark,
                }
            }));
        }

        return theme;
    }

    function getCurrentThemeId() {
        const html = document.documentElement;
        return safeGetStorage(STORAGE_KEY) || html.getAttribute('data-theme') || safeGetStorage(LEGACY_STORAGE_KEY) || 'light';
    }

    function initThemeSelector(selectId) {
        const id = selectId || 'appThemeSelect';
        const select = document.getElementById(id);
        if (!select) return;

        const registry = getRegistry();
        const fallback = getDefaultTheme(registry);
        const currentTheme = resolveTheme(getCurrentThemeId());

        select.innerHTML = '';
        (registry.length > 0 ? registry : [fallback]).forEach((theme) => {
            const option = document.createElement('option');
            option.value = theme.id;
            option.textContent = theme.name || theme.id;
            select.appendChild(option);
        });

        select.value = currentTheme.id;
        select.addEventListener('change', (event) => {
            applyTheme(event.target.value);
        });
    }

    function bootstrap() {
        const registry = getRegistry();
        const fallback = getDefaultTheme(registry);
        const storedTheme = safeGetStorage(STORAGE_KEY);
        const legacyTheme = safeGetStorage(LEGACY_STORAGE_KEY);

        let initialThemeId = storedTheme;
        if (!initialThemeId && legacyTheme) {
            initialThemeId = legacyTheme === 'dark' ? 'dark' : 'light';
        }
        if (!initialThemeId) {
            initialThemeId = getCurrentThemeId();
        }

        applyTheme(initialThemeId, { persist: true, emit: false });
    }

    window.ThemeManager = {
        applyTheme,
        bootstrap,
        initThemeSelector,
        getThemes: getRegistry,
        getCurrentThemeId,
    };
})();
