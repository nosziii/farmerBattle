<template>
  <div class="group relative overflow-hidden rounded-2xl bg-surface p-6 border-2 border-secondary-700/50 shadow-lg hover:shadow-secondary-500/10 hover:border-secondary-500/50 transition-all duration-300 hover:scale-105">
    <div class="absolute -top-10 -right-10 w-40 h-40 bg-secondary-500/10 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700"></div>

    <div class="relative z-10">
      <div class="relative mb-5">
        <div class="relative w-full h-40 rounded-xl bg-secondary-900 flex items-center justify-center overflow-hidden shadow-xl border-2 border-white/10">
          <span class="text-7xl drop-shadow-2xl">{{ icon }}</span>
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
          <div v-if="isUpgrading" class="absolute inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center">
            <div class="text-center">
              <div class="relative w-12 h-12 mx-auto mb-3">
                <div class="animate-spin rounded-full h-12 w-12 border-4 border-primary-500/30 border-t-primary"></div>
              </div>
              <p class="text-sm text-white font-bold">{{ upgradeTime }}</p>
            </div>
          </div>
        </div>
        <div class="absolute -top-3 -right-3 bg-gradient-to-br from-primary to-primary-700 text-white rounded-xl w-14 h-14 flex items-center justify-center font-bold text-xl shadow-lg shadow-primary-500/50 border-2 border-white/20">
          {{ level }}
        </div>
      </div>

      <h3 class="text-xl font-bold text-text-primary mb-2">{{ name }}</h3>
      <p class="text-sm text-text-secondary mb-5 leading-relaxed">{{ description }}</p>

      <div class="text-sm text-text-secondary mb-3">
        <p>Cost: {{ cost_wood }} Wood, {{ cost_clay }} Clay, {{ cost_iron }} Iron</p>
      </div>

      <button
        @click="emitUpgrade"
        :disabled="isUpgrading || !canAfford"
        :class="`w-full py-3 px-5 rounded-xl font-bold text-base shadow-lg transition-all duration-300 border-2 ${
          isUpgrading || !canAfford
            ? 'bg-gray-700/50 text-gray-500 cursor-not-allowed border-gray-600/30'
            : 'bg-primary text-white hover:bg-primary-600 hover:scale-105 hover:shadow-primary-500/50 border-primary-400/30'
        }`"
      >
        {{ isUpgrading ? 'Upgrading...' : `Upgrade to Level ${level + 1}` }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  name: string;
  description: string;
  icon: string;
  level: number;
  isUpgrading?: boolean;
  upgradeTime?: string;
  cost_wood: number;
  cost_clay: number;
  cost_iron: number;
  canAfford: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits(['upgrade']);

function emitUpgrade() {
  emit('upgrade', props.name);
}
</script>
