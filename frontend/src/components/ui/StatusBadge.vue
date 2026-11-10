<script setup lang="ts">
withDefaults(defineProps<{ tone?: 'neutral' | 'success' | 'warning' | 'danger' }>(), { tone: 'neutral' })
</script>

<template><span class="status-badge" :class="`status-badge--${tone}`"><slot /></span></template>
