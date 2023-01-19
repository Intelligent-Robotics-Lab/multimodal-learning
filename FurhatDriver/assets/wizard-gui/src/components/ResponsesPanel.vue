<template>
  <div class="rounded p-4 bg-white columns-1">
    <h1 class="text-3xl mb-4">Responses</h1>
    <div class="grid grid-cols-4 gap-2">
      <div v-for="response in responses" :key="response.script" class="w-full"
        :class="{ 'col-span-4': response.script.length > 30, 'col-span-2': response.script.length > 15 && response.script.length <= 30 }">
        <button class="rounded border border-teal-400 p-2 hover:bg-teal-200 text-teal-800 w-full" :class="{'bg-white': response.soft, 'bg-teal-50': !response.soft}"
          @click="runResponse(response)">
          {{ response.script }}
        </button>
      </div>
      <div v-for="gesture in gestures" :key="gesture.name" class="w-full">
        <button class="rounded border border-teal-400 bg-teal-50 p-2 hover:bg-teal-200 text-teal-800 w-full"
          @click="runGesture(gesture)">
          ({{ gesture.name }})
        </button>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, watch, computed } from "vue";
import { Furhat } from "furhat-gui";

class Response {
  script: string;
  soft: boolean;
  constructor(script: string, soft: boolean = false) {
    this.script = script;
    this.soft = soft;
  }
}

class Gesture {
  name: string;
  constructor(name: string) {
    this.name = name;
  }
}
const props = defineProps({
  furhat: Furhat,
  job: {
    type: String,
    required: true
  }
})

const generalResponses = [
  new Response("Thank you for your time today, it was nice to meet you. We will review your fitness for this position and respond with a decision soon"),
  new Response("Tell me more about that"),
  new Response("How are you today?"),
  new Response("I'm feeling very good, thank you"),
  new Response("Bye, have a good day!"),
  new Response("Wow, that's amazing"),
  new Response('Sounds good'),
  new Response('Yeah', true),
  new Response('Nice', true),
  new Response('Right', true),
  new Response('Huh', true),
  new Response('Hmm', true),
  new Response('Perfect'),
  new Response('A huh', true)];
const jobResponses = new Map<string, Response[]>([
  ["Petsmart", [
    new Response("Hi, I am Furhat, I will be interviewing you today for a position at Petsmart"), 
    new Response("Have you cared for pets before?"),
    new Response("Tell me about some pets you would recommend to beginners")]],
  ["5th/3rd Bank", [
    new Response("Hi, I am Furhat, I will be interviewing you today for a position at 5th/3rd Bank"),
    new Response("What is your experience with personal finance?")
  ]],
  ["Barnes and Noble", [
    new Response("Hi, I am Furhat, I will be interviewing you today for a position at Barnes and Noble"),
    new Response("What type of books do you like to read?")
  ]],
]);
const responses = computed(() => {
  let concat = generalResponses.concat(jobResponses.get(props.job) || []);
  return concat.sort((a, b) => b.script.length - a.script.length);
})
const gestures: Gesture[] = reactive([new Gesture('Nod')]);

const runResponse = (response: Response) => {
  if (props.furhat) {
    let output = response.soft ? `<prosody volume="-12dB">${response.script}</prosody>` : response.script;
    props.furhat.send({
      event_name: 'Ask',
      data: output,
      script: response.script,
      volume: response.soft ? 0.5 : 1,
    })
  }
}

const runGesture = (gesture: Gesture) => {
  console.log("running gesture", gesture.name)
  if (props.furhat) {
    props.furhat.gesture(gesture.name);
  }
}

</script>
<style lang=""></style>
