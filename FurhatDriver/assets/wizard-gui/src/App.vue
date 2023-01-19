<script setup lang="ts">
// import HelloWorld from "./components/HelloWorld.vue";
// import TheWelcome from "./components/TheWelcome.vue";
import "./index.css";
// import "./assets/logo.png";
import InterviewQuestion from "./components/InterviewQuestion.vue";
import ResponsesPanel from "./components/ResponsesPanel.vue";
import FreetypePanel from "./components/FreetypePanel.vue";
import TranscriptPanel from "./components/TranscriptPanel.vue";
import ControlPanel from "./components/ControlPanel.vue";
import { Furhat } from "furhat-gui";
import DevFurhatGUI from "./furhat-dev";
import { ref, reactive, watch } from "vue";

// let furhat: Furhat = reactive(new Furhat("", 0, "")) as Furhat;
let furhat: Furhat = new Furhat("", 0, "");
let connected = ref(false);

let makeFurhatGUI: () => Promise<Furhat>;
if (import.meta.env.DEV) {
  makeFurhatGUI = DevFurhatGUI;
} else {
  makeFurhatGUI = DevFurhatGUI;
}
makeFurhatGUI()
  .then((f) => {
    console.log("Connected to Furhat skill");
    console.log(f);
    Object.assign(furhat, f);
    console.log(furhat);
    furhat.onConnectionError((ev: Event) => {
      console.error("Error occured while connecting to Furhat skill");
      connected.value = false;
    });
    furhat.onConnectionClose(() => {
      console.warn("Connection with Furhat skill has been closed");
      connected.value = false;
    });
  }).then(() => {
    connected.value = true;
  })
  .catch((error) => {
      console.error("Error occured while connecting to Furhat skill", error);
      connected.value = false;
  });
  
</script>

<template>
<div class="flex flex-col h-full">
  <div class="p-4 flex flex-row space-x-4 items-center">
    <img src="./assets/logo.png" class="w-12 h-12" />
    <h1 class="text-4xl flex-grow">ITL Experiment</h1>
  </div>
  <div class="bg-slate-100 p-4 flex-grow overflow-hidden">
    <div class="w-full h-full grid grid-cols-2 gap-4">
      <div class="rounded p-4 bg-white" v-if="!connected">
        <h1 class="text-3xl mb-4">Connecting...</h1>
      </div>
      <ControlPanel v-if="connected" :furhat="furhat" class="h-full"></ControlPanel>
      <TranscriptPanel v-if="connected" :furhat="furhat" class="h-full overflow-hidden"></TranscriptPanel>
    </div>
  </div>
</div>
</template>

<style>
</style>
