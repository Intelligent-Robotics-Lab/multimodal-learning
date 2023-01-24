<template>
  <div class="rounded p-4 bg-white flex flex-col items-center gap-4">
    <h1 class="text-3xl w-full">Transcript</h1>
    <div class="w-full p-4 rounded-md border-slate-200 border-2 overflow-y-scroll flex-grow flex flex-col-reverse">
      <div class="w-full space-y-2">
        <div v-for="utterance in utterances" class="w-full flex flex-row"
          :class="{ 'justify-start': utterance.speaker == Speaker.Human, 'justify-end': utterance.speaker == Speaker.Robot }">
          <div class="rounded-tl-lg rounded-tr-lg py-2 px-4"
            :class="utterance.speaker == Speaker.Human ? { 'bg-purple-100': true, 'text-purple-900': true, 'rounded-br-lg': true} : { 'bg-purple-600': true, 'text-white': true, 'rounded-bl-lg': true }">
            <h4>{{ utterance.text }}</h4>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive } from "vue";
import { Furhat } from "furhat-gui";
enum Speaker {
  Robot,
  Human,
}
class Utterance {
  speaker: Speaker;
  text: string;
  interim: boolean;
  constructor(speaker: Speaker, text: string, interim: boolean) {
    this.speaker = speaker;
    this.text = text;
    this.interim = interim;
  }
}
const utterances: Utterance[] = reactive([]);
let addUtterance = (utterance: Utterance) => {
  if (utterances[utterances.length - 1] && utterances[utterances.length - 1].interim) {
    utterances.pop();
  }
  utterances.push(utterance);
};
const props = defineProps({
  furhat: Furhat,
})
if (props.furhat) {
  props.furhat.subscribe('Ask', (event) => {
    addUtterance(new Utterance(Speaker.Robot, event.script ? event.script : event.data, false));
  })
  props.furhat.subscribe('Say', (event) => {
    addUtterance(new Utterance(Speaker.Human, event.data, false));
  })
  props.furhat.subscribe('furhatos.event.senses.SenseSpeech', (event) => {
    console.log(event);
    if (event.displayText == '') {
      addUtterance(new Utterance(Speaker.Human, '(No Response)', false));
      return;
    }
    addUtterance(new Utterance(Speaker.Human, event.displayText, !!event.type));
  })
  props.furhat.subscribe('furhatos.event.monitors.MonitorSpeechStart', (event) => {
    console.log(event);
    if (event.displayText == '') {
      addUtterance(new Utterance(Speaker.Robot, '(No Response)', false));
      return;
    }
    addUtterance(new Utterance(Speaker.Robot, event.diplayText, false));
  })
  // props.furhat.subscribe('InterimSpeech', (event) => {
  //   addUtterance(new Utterance(Speaker.Human, event.text, true));
  // })
}
</script>
<style lang=""></style>
