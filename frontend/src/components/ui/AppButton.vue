<script setup lang="ts">
withDefaults(defineProps<{ variant?: 'primary' | 'secondary' | 'ghost'; type?: 'button' | 'submit' | 'reset'; disabled?: boolean }>(), { variant: 'primary', type: 'button', disabled: false })
</script>

<template><button class="button" :class="`button--${variant}`" :type="type" :disabled="disabled"><slot /></button></template>
