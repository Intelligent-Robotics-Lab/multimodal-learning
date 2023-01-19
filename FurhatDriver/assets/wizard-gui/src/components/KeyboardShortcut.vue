<template>
  <div class="border-2 border-black rounded-md h-8 w-8 flex justify-center items-center">
    <p class="">
      {{ shortcut }}
    </p>
  </div>
</template>
<script lang="ts">
let blocked = false

export default {
  props: ['shortcut'],
  emits: ['activated'],
  setup(props: any, ctx: any) {
    window.addEventListener('keydown', (e) => {
      if (!blocked && e.key === props.shortcut) {
        e.preventDefault()
        ctx.emit('activated')
      }
    })
  },
}

export const blockInput = () => {
  blocked = true
}

export const unblockInput = () => {
  blocked = false
}
</script>
<style lang=""></style>
