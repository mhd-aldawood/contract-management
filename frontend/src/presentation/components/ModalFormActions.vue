<script setup>
import { inject } from 'vue'

// Keep form actions in the shared dialog footer, or inline on standalone forms.
const target = inject('modal-actions-target', null)
</script>

<template>
  <Teleport :to="target || 'body'" :disabled="!target" defer>
    <div class="agreement-form-actions"><slot /></div>
  </Teleport>
</template>
