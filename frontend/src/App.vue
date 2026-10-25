<template>
  <div class="app-root" :class="{ 'app-root--authenticated': showShell }">
    <AppToolbar v-if="showShell" />
    <div class="app-main"><router-view :key="route.path" /></div>
  </div>
  <NotificationHost />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppToolbar from '@/presentation/components/AppToolbar.vue'
import NotificationHost from '@/presentation/components/NotificationHost.vue'

const route = useRoute()
const showShell = computed(() => route.meta.requiresAuth && !route.meta.allowPasswordChange)
</script>
