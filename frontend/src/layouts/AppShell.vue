<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '../components/layout/AppSidebar.vue'
import AppTopbar from '../components/layout/AppTopbar.vue'

const route = useRoute()
const drawerOpen = ref(false)
const drawer = ref<HTMLElement | null>(null)

async function openDrawer() {
  drawerOpen.value = true
  await nextTick()
  drawer.value?.querySelector<HTMLElement>('a, button')?.focus()
}

function closeDrawer(restoreFocus = true) {
  drawerOpen.value = false
  if (restoreFocus) nextTick(() => document.querySelector<HTMLButtonElement>('.menu-trigger')?.focus())
}

function onDrawerNavigate() {
  closeDrawer(false)
  nextTick(() => document.querySelector<HTMLElement>('#main-content')?.focus())
}

function trapFocus(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    closeDrawer()
    return
  }
  if (event.key !== 'Tab' || !drawerOpen.value || !drawer.value) return
  const focusable = [...drawer.value.querySelectorAll<HTMLElement>('a[href], button:not(:disabled)')]
  if (focusable.length === 0) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

watch(() => route.fullPath, () => closeDrawer(false))
</script>

<template>
  <div class="app-frame" @keydown="trapFocus">
    <a class="skip-link" href="#main-content">Skip to main content</a>
    <div v-if="drawerOpen" class="drawer-backdrop" @click="closeDrawer()" />
    <aside
      ref="drawer"
      class="sidebar-region"
      :class="{ 'sidebar-region--open': drawerOpen }"
      :role="drawerOpen ? 'dialog' : undefined"
      :aria-modal="drawerOpen ? 'true' : undefined"
      :aria-hidden="!drawerOpen && undefined"
      :inert="!drawerOpen && undefined"
      aria-label="Main navigation"
    >
      <AppSidebar @navigate="onDrawerNavigate" />
    </aside>
    <div class="workspace">
      <AppTopbar :title="route.meta.title ?? 'MyHarf OS'" :drawer-open="drawerOpen" @open-menu="openDrawer" />
      <main id="main-content" class="main-content" tabindex="-1">
        <RouterView />
      </main>
      <footer class="app-footer">MyHarf OS <span>·</span> Internal operations workspace</footer>
    </div>
  </div>
</template>
