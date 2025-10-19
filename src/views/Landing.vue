<template>
  <main class="flex-1 overflow-y-auto bg-gradient-to-b from-background via-background/80 to-secondary-900/40">
    <section class="mx-auto flex max-w-5xl flex-col items-center justify-center gap-8 px-6 py-20 text-center">
      <span class="rounded-full border border-primary/40 bg-primary/20 px-4 py-1 text-xs uppercase tracking-[0.35em] text-primary-200">
        Welcome Commander
      </span>
      <h2 class="text-4xl font-bold md:text-5xl">
        Forge your <span class="text-primary-300">village</span>, train mighty armies, and dominate the world map.
      </h2>
      <p class="max-w-2xl text-base text-text-secondary md:text-lg">
        Farmer Battle blends chill village management with strategic warfare. Gather resources, upgrade your buildings,
        and lead your troops to victory against rivals and roaming barbarians.
      </p>
      <div class="flex flex-col gap-3 sm:flex-row">
        <router-link
          to="/register"
          class="rounded-xl border border-primary/60 bg-primary/80 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-primary/30 transition hover:bg-primary"
        >
          Start your village
        </router-link>
        <router-link
          to="/login"
          class="rounded-xl border border-secondary-700/50 bg-secondary-800/70 px-6 py-3 text-base font-semibold text-text-secondary transition hover:bg-secondary-800 hover:text-text-primary"
        >
          Sign in
        </router-link>
      </div>
    </section>

    <section class="mx-auto grid max-w-5xl gap-6 px-6 pb-20 md:grid-cols-3">
      <article class="rounded-2xl border border-secondary-700/40 bg-surface/70 p-6 shadow-lg shadow-black/20 backdrop-blur">
        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary/20 text-2xl">🏡</div>
        <h3 class="text-xl font-semibold text-text-primary">Evolve Your Settlement</h3>
        <p class="mt-2 text-sm text-text-secondary">
          Upgrade production buildings, balance storage, and keep your citizens thriving while you plan your next move.
        </p>
      </article>
      <article class="rounded-2xl border border-secondary-700/40 bg-surface/70 p-6 shadow-lg shadow-black/20 backdrop-blur">
        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/20 text-2xl">⚔️</div>
        <h3 class="text-xl font-semibold text-text-primary">Train Elite Troops</h3>
        <p class="mt-2 text-sm text-text-secondary">
          Unlock powerful units, coordinate training queues, and customize your army composition for offense or defense.
        </p>
      </article>
      <article class="rounded-2xl border border-secondary-700/40 bg-surface/70 p-6 shadow-lg shadow-black/20 backdrop-blur">
        <div class="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/20 text-2xl">🗺️</div>
        <h3 class="text-xl font-semibold text-text-primary">Conquer the World Map</h3>
        <p class="mt-2 text-sm text-text-secondary">
          Expand your influence, claim strategic tiles, and climb the global leaderboard against other commanders.
        </p>
      </article>
    </section>

    <section class="bg-secondary-900/60 py-16">
      <div class="mx-auto flex max-w-5xl flex-col gap-8 px-6 md:flex-row md:items-center md:justify-between">
        <div>
          <h3 class="text-2xl font-semibold text-text-primary">Already training troops?</h3>
          <p class="mt-2 text-sm text-text-secondary">
            Sign in to resume construction, manage your armies, and survey the realm.
          </p>
        </div>
        <router-link
          to="/login"
          class="inline-flex items-center rounded-xl border border-primary/50 bg-primary/80 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-primary/20 transition hover:bg-primary"
        >
          Resume command
        </router-link>
      </div>
    </section>
  </main>
</template>
