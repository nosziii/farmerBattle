import { App, ComputedRef, computed, inject, reactive } from 'vue';
import en from '../locales/en';
import hu from '../locales/hu';

export type Locale = 'en' | 'hu';

export interface MessageTree {
  [key: string]: string | MessageTree;
}

export interface I18nContext {
  locale: ComputedRef<Locale>;
  availableLocales: Locale[];
  setLocale: (next: Locale) => void;
  t: (key: string, values?: Record<string, string | number>) => string;
}

const I18N_SYMBOL = Symbol('i18n');
const STORAGE_KEY = 'fb_locale';

const messages: Record<Locale, MessageTree> = {
  en,
  hu,
};

const isLocale = (value: string): value is Locale => value === 'en' || value === 'hu';

const getNestedValue = (tree: MessageTree, path: string[]): string | MessageTree | undefined => {
  return path.reduce<string | MessageTree | undefined>((acc, segment) => {
    if (typeof acc !== 'object' || acc === null) {
      return undefined;
    }
    return (acc as MessageTree)[segment];
  }, tree);
};

const template = (input: string, params?: Record<string, string | number>) => {
  if (!params) return input;
  return input.replace(/\{(\w+)\}/g, (match, key) => {
    const value = params[key];
    return value !== undefined ? String(value) : match;
  });
};

const createI18nState = () => {
  const stored = (typeof window !== 'undefined' && window.localStorage.getItem(STORAGE_KEY)) || '';
  const initialLocale: Locale = isLocale(stored) ? stored : 'en';
  const state = reactive({
    locale: initialLocale as Locale,
  });

  const setLocale = (next: Locale) => {
    if (!messages[next]) return;
    state.locale = next;
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, next);
      document.documentElement.setAttribute('lang', next);
    }
  };

  if (typeof document !== 'undefined') {
    document.documentElement.setAttribute('lang', state.locale);
  }

  const t = (key: string, values?: Record<string, string | number>) => {
    const segments = key.split('.');
    const message = getNestedValue(messages[state.locale], segments);
    if (typeof message === 'string') {
      return template(message, values);
    }
    const fallback = getNestedValue(messages.en, segments);
    if (typeof fallback === 'string') {
      return template(fallback, values);
    }
    return key;
  };

  return {
    locale: computed(() => state.locale),
    setLocale,
    availableLocales: Object.keys(messages) as Locale[],
    t,
  };
};

const state = createI18nState();

export const installI18n = (app: App) => {
  app.provide(I18N_SYMBOL, state);
};

export const useI18n = (): I18nContext => {
  const context = inject<I18nContext>(I18N_SYMBOL as unknown as symbol);
  if (!context) {
    throw new Error('i18n context has not been provided');
  }
  return context;
};

export const i18n = state;
