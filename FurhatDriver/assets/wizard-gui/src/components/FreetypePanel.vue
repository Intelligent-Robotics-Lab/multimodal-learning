<script setup lang="ts">
import { Furhat } from "furhat-gui";
import { ref, onMounted } from "vue";
import KeyboardShortcut, {blockInput, unblockInput} from "./KeyboardShortcut.vue";

let outputText = ref('')
const inputRef = ref<HTMLInputElement>()
const buttonRef = ref<HTMLButtonElement>()
let focused = false

const props = defineProps({
  furhat: Furhat,
})

const sayText = (text: string) => {
  if (props.furhat) {
    props.furhat.send({
        event_name: 'Ask',
        data: text
    })
  } else {
    console.info("Furhat would say:", text)
  }
}

const submit = () => {
  console.log("Submitting:", inputRef.value)
  if (outputText.value) {
    sayText(outputText.value)
    buttonRef.value!.focus()
    outputText.value = ''
  }
}

</script>
<template>
  <div class="rounded p-4 bg-white columns-1" @keydown.enter="submit">
    <div class="w-full flex flex-row gap-4 items-center mb-4">
      <h1 class="text-3xl">Free Type</h1>
      <KeyboardShortcut :shortcut="'t'" @activated="inputRef!.focus()"></KeyboardShortcut>
    </div>
    <div class="flex flex-row space-x-4">
      <input type="text" @focus="blockInput()" @blur="unblockInput()" v-model="outputText" ref="inputRef" class="grow rounded border border-purple-400 px-4" />
      <button ref="buttonRef"
        class="w-20 rounded border border-purple-400 text-purple-600 p-2 hover:bg-purple-600 hover:text-white font-bold"
        @click="submit()">
        Send
      </button>
    </div>
  </div>
</template>
<!-- <style lang=""></style> -->
