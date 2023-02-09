<script setup lang="ts">

import "./index.css";
// import OperatorPanel from "./components/OperatorPanel.vue";
// import UserPanel from "./components/UserPanel.vue";
import { RouterView } from 'vue-router'

// import FurhatGUI, { Furhat } from "furhat-gui";
// import DevFurhatGUI from "./furhat-dev";
// import { ref, reactive, watch } from "vue";

// // let furhat: Furhat = reactive(new Furhat("", 0, "")) as Furhat;
// let furhat: Furhat = new Furhat("", 0, "");
// let connected = ref(false);

// let makeFurhatGUI: () => Promise<Furhat>;
// if (import.meta.env.DEV) {
//   makeFurhatGUI = DevFurhatGUI;
// } else {
//   makeFurhatGUI = FurhatGUI;
// }
// makeFurhatGUI()
//   .then((f) => {
//     console.log("Connected to Furhat skill");
//     console.log(f);
//     Object.assign(furhat, f);
//     console.log(furhat);
//     furhat.onConnectionError((ev: Event) => {
//       console.error("Error occured while connecting to Furhat skill");
//       connected.value = false;
//     });
//     furhat.onConnectionClose(() => {
//       console.warn("Connection with Furhat skill has been closed");
//       connected.value = false;
//     });
//   }).then(() => {
//     connected.value = true;
//   })
//   .catch((error) => {
//       console.error("Error occured while connecting to Furhat skill", error);
//       connected.value = false;
//   });

</script>

<template>
<div class="flex flex-col h-full">
  <div class="p-4 flex flex-row space-x-4 items-center">
    <img src="./assets/logo.png" class="w-12 h-12" />
    <h1 class="text-4xl flex-grow">ITL Experiment</h1>
  </div>
  <div class="bg-slate-100 p-4 flex-grow overflow-hidden">
    <router-view></router-view>
  </div>
</div>
</template>

<style>
</style>
