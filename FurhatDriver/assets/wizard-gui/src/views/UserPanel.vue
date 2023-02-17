<script setup lang="ts">
import TranscriptPanel from "@/components/TranscriptPanel.vue";
import ControlPanel from "@/components/ControlPanel.vue";
import FurhatGUI, { Furhat } from "furhat-gui";
import DevFurhatGUI from "../furhat-dev";
import { ref, reactive, watch } from "vue";

let furhat: Furhat = new Furhat("", 0, "");
let connected = ref(false);

let makeFurhatGUI: () => Promise<Furhat>;
if (import.meta.env.DEV) {
  makeFurhatGUI = DevFurhatGUI;
} else {
  makeFurhatGUI = FurhatGUI;
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

<div class="w-full h-full grid grid-cols-2 gap-4">
  <div class="rounded p-4 bg-white" v-if="!connected">
    <h1 class="text-3xl mb-4">Connecting...</h1>
  </div>
  <TranscriptPanel v-if="connected" :furhat="furhat" class="h-full overflow-hidden"></TranscriptPanel>
</div>

</template>

<style>
</style>
