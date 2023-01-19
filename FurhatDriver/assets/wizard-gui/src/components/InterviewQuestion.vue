<template>
  <div class="rounded p-4 bg-white flex flex-col items-center gap-4">
    <h1 class="text-3xl w-full">Interview Questions</h1>
    <div class="space-y-2 grow h-full w-full pr-4 overflow-y-scroll">
      <div v-for="(question, index) in questions.get(currentDifficulty)" :key="question"
        class="w-full flex flex-row gap-4 items-center">
        <button class="rounded border border-green-400 bg-green-50 p-2 hover:bg-green-200 text-green-600 grow"
          @click="sayText(question)">
          {{ question }}
        </button>
        <KeyboardShortcut v-if="index < 10" :shortcut="((index + 1) == 10 ? 0 : index + 1).toString()" @activated="sayText(question)"></KeyboardShortcut>
        <div v-if="index >= 10" class="h-8 w-8"></div>
      </div>
    </div>
    <ItemSelector :options="[...questions.keys()]" v-model="currentDifficulty" class="w-1/2"></ItemSelector>
  </div>
</template>
<script setup lang="ts">
import { reactive, ref } from "vue";
import { Furhat } from "furhat-gui";
import KeyboardShortcut from "./KeyboardShortcut.vue";
import ItemSelector from "./ItemSelector.vue";

const questions = reactive(new Map<string, string[]>());
questions.set("Easy", [
  "Tell me about yourself",
  "What are your strengths?",
  "What is one of your weaknesses?",
  "What makes you a good candidate for this position?",
  "Where do you see yourself in 5 years?",
  "Do you have any questions for me?"
]);
questions.set("Medium", [
  "Tell me about yourself",
  "What are your strengths?",
  "What is one of your weaknesses?",
  "Why should we hire you?",
  "How would you handle an upset customer?",
  "Tell me about a time you worked as part of a team",
  "Where do you see yourself in 5 years?",
  "Do you have any questions for me?"
])
questions.set("Hard", [
  "Tell me about yourself",
  "What are your strengths?",
  "What is one of your weaknesses?",
  "Why should we hire you?",
  "How would you handle an upset customer?",
  "Tell me about a time you worked as part of a team",
  "Where do you see yourself in 5 years?",
  "Tell me about a time you took initiative",
  "Tell me about a time you learned from your mistake",
  "Tell me about your proudest accomplishment",
  "Do you have any questions for me?"
])
questions.set("Friendly Chat", [
  "How was your day?",
  "I see you are happy today",
  "Wow, that's amazing!",
  "Not bad",
  "What's your schedule tomorrow?",
  "Haha that's funny",
])
const difficulties = reactive([
  "Easy", "Medium", "Hard", "Friendly Chat"
]);
const props = defineProps({
  furhat: Furhat,
})
const currentDifficulty = ref('')
const sayText = (text: string) => {
  if (props.furhat) {
    props.furhat.send({
      event_name: 'Ask',
      data: text
    })
  }
}
</script>
<style lang=""></style>
