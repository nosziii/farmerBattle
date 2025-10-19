<template>
  <main class="flex-1 overflow-y-auto bg-gradient-to-b from-background via-background/80 to-secondary-900/40">
    <section class="mx-auto flex max-w-5xl flex-col items-center justify-center gap-8 px-6 py-20 text-center">
      <span class="rounded-full border border-primary/40 bg-primary/20 px-4 py-1 text-xs uppercase tracking-[0.35em] text-primary-200">
        {{ t('landing.hero.badge') }}
      </span>
      <h2 class="text-4xl font-bold md:text-5xl">
        {{ t('landing.hero.title.prefix') }}<span class="text-primary-300">{{ t('landing.hero.title.highlight') }}</span>{{ t('landing.hero.title.suffix') }}
      </h2>
      <p class="max-w-2xl text-base text-text-secondary md:text-lg">
        {{ t('landing.hero.description') }}
      </p>
      <div class="flex flex-col gap-3 sm:flex-row">
        <router-link
          to="/register"
          class="rounded-xl border border-primary/60 bg-primary/80 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-primary/30 transition hover:bg-primary"
        >
          {{ t('landing.hero.ctaStart') }}
        </router-link>
        <router-link
          to="/login"
          class="rounded-xl border border-secondary-700/50 bg-secondary-800/70 px-6 py-3 text-base font-semibold text-text-secondary transition hover:bg-secondary-800 hover:text-text-primary"
        >
          {{ t('landing.hero.ctaSignIn') }}
        </router-link>
      </div>
    </section>

    <section class="mx-auto grid max-w-5xl gap-6 px-6 pb-20 md:grid-cols-3">
      <article class="rounded-2xl border border-secondary-700/40 bg-surface/70 p-6 shadow-lg shadow-black/20 backdrop-blur">
        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/20 text-2xl">🏡</div>
        <h3 class="text-xl font-semibold text-text-primary">{{ t('landing.features.settlement.title') }}</h3>
        <p class="mt-2 text-sm text-text-secondary">
          {{ t('landing.features.settlement.description') }}
        </p>
      </article>
      <article class="rounded-2xl border border-secondary-700/40 bg-surface/70 p-6 shadow-lg shadow-black/20 backdrop-blur">
        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/20 text-2xl">⚔️</div>
        <h3 class="text-xl font-semibold text-text-primary">{{ t('landing.features.troops.title') }}</h3>
        <p class="mt-2 text-sm text-text-secondary">
          {{ t('landing.features.troops.description') }}
        </p>
      </article>
      <article class="rounded-2xl border border-secondary-700/40 bg-surface/70 p-6 shadow-lg shadow-black/20 backdrop-blur">
        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/20 text-2xl">🗺️</div>
        <h3 class="text-xl font-semibold text-text-primary">{{ t('landing.features.world.title') }}</h3>
        <p class="mt-2 text-sm text-text-secondary">
          {{ t('landing.features.world.description') }}
        </p>
      </article>
    </section>

    <section class="bg-secondary-900/60 py-16">
      <div class="mx-auto flex max-w-5xl flex-col gap-8 px-6 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 class="text-2xl font-semibold text-text-primary">{{ t('landing.resume.title') }}</h3>
          <p class="mt-2 text-sm text-text-secondary">
            {{ t('landing.resume.description') }}
          </p>
        </div>
        <router-link
          to="/login"
          class="inline-flex items-center rounded-xl border border-primary/50 bg-primary/80 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-primary/20 transition hover:bg-primary"
        >
          {{ t('landing.resume.cta') }}
        </router-link>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { useI18n } from "../i18n";

const { t } = useI18n();
</script>
