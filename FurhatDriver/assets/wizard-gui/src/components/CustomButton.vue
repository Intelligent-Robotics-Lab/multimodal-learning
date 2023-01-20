<template>
    <button class="rounded border p-2 w-full"
            :class="getStyle"
            :enabled="enabled"
            :highlighted="highlighted"
            @click="$emit('buttonClick')">
            <slot></slot>
    </button>
</template>

<script setup lang="ts">
import { computed } from "vue";
const props = defineProps({
    color: {
        type: String,
        required: true
    },
    enabled: {
        type: Boolean,
        default: true
    },
    highlighted: {
        type: Boolean,
        default: false
    }
})

const getStyle = computed(() => {
    if (!props.enabled) {
        return {
            'border-gray-400': true,
            'bg-gray-200': true,
            'text-gray-800': true,
        }
    }

    const style: {[key: string]: boolean} = {};
    style[`border-${props.color}-400`] = true;
    if (props.highlighted) {
        style[`bg-${props.color}-200`] = true;
    } else {
        style[`bg-${props.color}-50`] = true;
    }
    style[`text-${props.color}-800`] = true;
    return style;
})
</script>