<template>
  <div class="rounded-lg bg-slate-200 flex flex-row">
    <div v-for="option in options" :key="option" @click="emit('update:modelValue', option)" class="cursor-default rounded-lg px-4 py-2 grow flex justify-center items-center"
      :class="option == modelValue ? { 'bg-green-500': true, 'text-white': true } : { 'text-slate-400': true }">
      {{ option }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { PropType } from 'vue'
const active = ref('')
const props = defineProps({
  options: {
    type: Array as PropType<Array<string>>,
    required: true
  },
  modelValue: String
})
const emit = defineEmits<{ (event: 'update:modelValue', value: String): void }>()
onMounted(() => {
  if (props.options.length > 0) {
    emit('update:modelValue', props.options[0])
  }
})
</script>

<style scoped>
</style>