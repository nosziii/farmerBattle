<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue';
import type { PropType } from 'vue';
import axios from 'axios';
import type { BuildingStatus } from '../types/buildings';

const API_BASE = 'http://localhost:8000/api';
const villageId = 1;

const loading = ref(true);
const error = ref<string | null>(null);
const buildingStatuses = ref<BuildingStatus[]>([]);

const groupedBuildings = computed(() => {
  const sorted = [...buildingStatuses.value].sort((a, b) => a.order - b.order);
  const groups = new Map<string, BuildingStatus[]>();
  for (const status of sorted) {
    const bucket = groups.get(status.category) ?? [];
    bucket.push(status);
    groups.set(status.category, bucket);
  }
  return Array.from(groups.entries()).map(([category, items]) => ({
    category,
    items,
  }));
});

type TreeRequirement = {
  key: string;
  name: string;
  level: number;
};

type DependencyNode = {
  key: string;
  name: string;
  icon: string;
  children: DependencyNode[];
  alsoRequires: TreeRequirement[];
};

const dependencyForest = computed<DependencyNode[]>(() => {
  if (!buildingStatuses.value.length) {
    return [];
  }

  const byKey = new Map(buildingStatuses.value.map((status) => [status.internal_name, status]));
  const childrenMap = new Map<string, string[]>();

  buildingStatuses.value.forEach((status) => {
    status.requirements.forEach((requirement) => {
      const list = childrenMap.get(requirement.building) ?? [];
      list.push(status.internal_name);
      childrenMap.set(requirement.building, list);
    });
  });

  const roots = buildingStatuses.value
    .filter((status) => status.requirements.length === 0)
    .sort((a, b) => a.order - b.order)
    .map((status) => status.internal_name);

  const buildNode = (
    key: string,
    ancestry: Set<string>,
    parentKey: string | null
  ): DependencyNode | null => {
    if (ancestry.has(key)) {
      return null;
    }
    const status = byKey.get(key);
    if (!status) {
      return null;
    }
    const nextAncestry = new Set(ancestry);
    nextAncestry.add(key);

    const childNodes = (childrenMap.get(key) ?? [])
      .sort((a, b) => (byKey.get(a)?.order ?? 0) - (byKey.get(b)?.order ?? 0))
      .map((childKey) => buildNode(childKey, new Set(nextAncestry), key))
      .filter((child): child is DependencyNode => Boolean(child));

    const alsoRequires: TreeRequirement[] = status.requirements
      .filter((requirement) => requirement.building !== parentKey)
      .map((requirement) => ({
        key: requirement.building,
        name: byKey.get(requirement.building)?.name ?? requirement.display_name,
        level: requirement.required_level,
      }));

    return {
      key,
      name: status.name,
      icon: status.icon || '🏛️',
      children: childNodes,
      alsoRequires,
    };
  };

  return roots
    .map((root) => buildNode(root, new Set(), null))
    .filter((node): node is DependencyNode => Boolean(node));
});

const BuildingTreeNode = defineComponent({
  name: 'BuildingTreeNode',
  props: {
    node: {
      type: Object as PropType<DependencyNode>,
      required: true,
    },
  },
  setup(props) {
    const render = (): ReturnType<typeof h> =>
      h('li', { class: 'tree-node' }, [
        h('div', { class: 'tree-node__content' }, [
          h('div', { class: 'tree-node__title' }, [
            h('span', { class: 'tree-node__icon' }, props.node.icon || '🏛️'),
            h('span', { class: 'tree-node__name' }, props.node.name),
          ]),
          props.node.alsoRequires.length
            ? h(
                'div',
                { class: 'tree-node__requirements' },
                props.node.alsoRequires.map((requirement) =>
                  h(
                    'span',
                    {
                      class: 'tree-node__badge',
                      key: `${props.node.key}-${requirement.key}`,
                    },
                    `${requirement.name} Lv.${requirement.level}`
                  )
                )
              )
            : null,
        ]),
        props.node.children.length
          ? h(
              'ul',
              { class: 'tree-children' },
              props.node.children.map((child) =>
                h(BuildingTreeNode, {
                  node: child,
                  key: `${props.node.key}-${child.key}`,
                })
              )
            )
          : null,
      ]);

    return { render };
  },
});

const fetchBuildingData = async () => {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await axios.get<BuildingStatus[]>(
      `${API_BASE}/villages/${villageId}/buildings`
    );
    buildingStatuses.value = data ?? [];
  } catch (err: any) {
    console.error('Unable to load building info:', err);
    error.value =
      err.response?.data?.detail ??
      'We could not load the building handbook right now. Please try again shortly.';
  } finally {
    loading.value = false;
  }
};

onMounted(fetchBuildingData);

const formatRequirement = (status: BuildingStatus) =>
  status.requirements.length
    ? status.requirements
        .map(
          (requirement) =>
            `${requirement.display_name} Lv. ${requirement.required_level}${
              requirement.met ? ' ✔︎' : ''
            }`
        )
        .join(', ')
    : 'No prerequisites';
</script>

<template>
  <main class="flex-1 overflow-y-auto p-8 md:p-12 space-y-10">
    <section
      class="relative overflow-hidden rounded-3xl border border-secondary-700/40 bg-gradient-to-br from-primary-900/40 via-secondary-900/80 to-secondary-900/90 px-8 py-10 shadow-2xl shadow-primary-900/20"
    >
      <div class="absolute -top-8 -right-6 h-40 w-40 rounded-full bg-primary/20 blur-3xl"></div>
      <div class="absolute bottom-0 left-1/2 h-48 w-48 -translate-x-1/2 rounded-full bg-secondary-500/10 blur-3xl"></div>
      <div class="relative z-10 max-w-3xl space-y-4">
        <p class="text-xs uppercase tracking-[0.4em] text-primary-200/80">
          Builder’s Handbook
        </p>
        <h1 class="text-4xl md:text-5xl font-semibold text-text-primary">
          Plan your rise to a thriving kingdom
        </h1>
        <p class="text-base md:text-lg text-text-secondary leading-relaxed">
          Every structure you raise unlocks new opportunities. Use this guide to understand
          how buildings interact, which upgrades open new troops or technologies, and how to
          prioritise your development path.
        </p>
      </div>
    </section>

    <section v-if="loading" class="text-center text-text-secondary py-20">
      <p>Compiling building schematics...</p>
    </section>

    <section
      v-else-if="error"
      class="rounded-2xl border border-red-500/40 bg-red-500/10 px-6 py-5 text-red-100"
    >
      {{ error }}
    </section>

    <section v-else class="space-y-10">
      <article
        v-for="group in groupedBuildings"
        :key="group.category"
        class="space-y-4"
      >
        <div class="flex items-center justify-between gap-4">
          <h2 class="text-2xl font-semibold text-text-primary">
            {{ group.category }}
          </h2>
          <span class="text-xs uppercase tracking-wide text-text-secondary/60">
            {{ group.items.length }} building{{ group.items.length === 1 ? '' : 's' }}
          </span>
        </div>

        <div class="grid gap-6 md:grid-cols-2">
          <div
            v-for="status in group.items"
            :key="status.internal_name"
            class="rounded-2xl border border-secondary-700/40 bg-secondary-900/60 px-6 py-5 shadow-lg shadow-black/20 transition hover:border-primary/40 hover:shadow-primary/20"
          >
            <div class="flex items-start gap-4 mb-4">
              <div
                class="grid h-12 w-12 place-items-center rounded-xl bg-secondary-800/80 text-2xl"
              >
                {{ status.icon || '🏛️' }}
              </div>
              <div class="space-y-1">
                <div class="flex items-center gap-2">
                  <h3 class="text-lg font-semibold text-text-primary">
                    {{ status.name }}
                  </h3>
                  <span
                    class="rounded-full border border-primary/40 bg-primary/10 px-2 py-[2px] text-[10px] uppercase tracking-wide text-primary-200"
                  >
                    Lv. {{ status.level }}/{{ status.max_level }}
                  </span>
                </div>
                <p class="text-sm text-text-secondary leading-relaxed">
                  {{ status.description }}
                </p>
              </div>
            </div>

            <div class="space-y-3 text-sm text-text-secondary">
              <div>
                <p class="text-[11px] uppercase tracking-wide text-text-secondary/60 mb-1">
                  Requirements
                </p>
                <p>
                  {{ formatRequirement(status) }}
                </p>
              </div>

              <div v-if="status.effects.length">
                <p class="text-[11px] uppercase tracking-wide text-text-secondary/60 mb-1">
                  Effects when upgraded
                </p>
                <ul class="space-y-1">
                  <li v-for="effect in status.effects" :key="effect" class="flex gap-2">
                    <span class="text-primary">•</span>
                    <span>{{ effect }}</span>
                  </li>
                </ul>
              </div>

              <div v-if="status.unlocks.length">
                <p class="text-[11px] uppercase tracking-wide text-text-secondary/60 mb-1">
                  Unlocks
                </p>
                <ul class="space-y-1">
                  <li v-for="unlock in status.unlocks" :key="unlock" class="flex gap-2">
                    <span class="text-primary">➜</span>
                    <span>{{ unlock }}</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </article>

      <section class="space-y-4">
        <div class="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <h2 class="text-2xl font-semibold text-text-primary">Dependency Trees</h2>
          <p class="text-sm text-text-secondary">
            Follow the branches to see which structures unlock the next tier. Requirements shown as badges must also be met.
          </p>
        </div>
        <div class="grid gap-6 md:grid-cols-2">
          <details
            v-for="root in dependencyForest"
            :key="root.key"
            class="tree-panel"
            :open="root.children.length > 0"
          >
            <summary class="tree-summary">
              <span class="tree-summary__icon">{{ root.icon }}</span>
              <span class="tree-summary__name">{{ root.name }}</span>
              <span class="tree-summary__tag" v-if="root.children.length === 0">Standalone</span>
            </summary>
            <div v-if="root.children.length" class="tree-wrapper">
              <ul class="tree-root">
                <BuildingTreeNode
                  v-for="child in root.children"
                  :key="child.key"
                  :node="child"
                />
              </ul>
            </div>
            <p v-else class="mt-3 text-sm text-text-secondary/80">
              This building has no dependent unlocks.
            </p>
          </details>
        </div>
      </section>
    </section>
  </main>
</template>

<style scoped>
.tree-panel {
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 1.25rem;
  background: rgba(15, 23, 42, 0.65);
  box-shadow: 0 20px 40px rgba(15, 15, 35, 0.35);
  padding: 1.25rem 1.5rem;
  backdrop-filter: blur(12px);
}

.tree-summary {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 600;
  color: var(--color-text-primary);
  cursor: pointer;
  list-style: none;
}

.tree-summary::-webkit-details-marker {
  display: none;
}

.tree-summary__icon {
  display: grid;
  place-items: center;
  font-size: 1.35rem;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 1rem;
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.tree-summary__tag {
  margin-left: auto;
  font-size: 0.7rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(203, 213, 225, 0.6);
}

.tree-wrapper {
  margin-top: 1rem;
  padding-left: 1.5rem;
}

.tree-root,
.tree-children {
  list-style: none;
  margin: 0;
  padding-left: 1.25rem;
  border-left: 1px solid rgba(148, 163, 184, 0.25);
}

.tree-node {
  position: relative;
  padding-left: 1.25rem;
  margin-bottom: 1.1rem;
}

.tree-node::before {
  content: '';
  position: absolute;
  left: -1.25rem;
  top: 0.9rem;
  width: 1.25rem;
  height: 1px;
  background: rgba(148, 163, 184, 0.25);
}

.tree-node__content {
  background: rgba(30, 41, 59, 0.65);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 1rem;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tree-node__title {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.tree-node__icon {
  display: grid;
  place-items: center;
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 0.8rem;
  background: rgba(148, 163, 184, 0.12);
  font-size: 1.2rem;
}

.tree-node__requirements {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: rgba(203, 213, 225, 0.8);
}

.tree-node__badge {
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 999px;
  padding: 0.2rem 0.65rem;
  background: rgba(56, 189, 248, 0.08);
  letter-spacing: 0.04em;
}
</style>
