<script setup lang="ts">
const props = defineProps<{
  title: string;
  description?: string;
}>();
</script>

<template>
  <main class="flex-1 p-8 overflow-y-auto">
    <section class="max-w-3xl mx-auto text-center py-24">
      <h1 class="text-4xl font-bold mb-4">{{ props.title }}</h1>
      <p class="text-lg text-text-secondary">
        {{ props.description ?? "This feature is still under construction. Check back soon!" }}
      </p>
    </section>
  </main>
</template>
