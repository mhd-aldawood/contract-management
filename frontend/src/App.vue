<template>
  <router-view />
  <NotificationHost />
</template>

<script setup>
import NotificationHost from '@/presentation/components/NotificationHost.vue'
</script>

<style>
* { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
body { margin: 0; }
</style>
