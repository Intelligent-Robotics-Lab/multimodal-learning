<template>
  <div class="rounded p-4 bg-white columns-1">
    <h1 class="text-3xl mb-4">Control</h1>
    <div class="grid grid-cols-4 gap-2">
      <h4 class="text-lg col-span-4">Connected to server: {{ stale ? "No" : "Yes" }}</h4>
      <h4 class="text-lg col-span-4">Participant Id:</h4>
      <div class="col-span-4">
        <input type="text" v-model="participantId" class="rounded border border-teal-400 p-2 text-teal-800">
      </div>
      <h4 class="text-lg col-span-4">Mode:</h4>
      <div v-for="mode in modes" :key="mode" class="w-full">
        <CustomButton color="teal" :enabled="currentITLMode == 'Idle'" :highlighted="currentMode == mode" @buttonClick="setMode(mode)">
          {{ mode }}
        </CustomButton>
      </div>
      <h4 v-if="currentMode == 'ITL'" class="text-lg col-span-4">ITL Mode:</h4>
      <div v-if="currentMode == 'ITL'" v-for="mode in ITLModes" :key="mode" class="w-full">
        <CustomButton color="purple" 
                      :enabled="currentITLMode == 'Idle' || currentITLMode == mode" 
                      :highlighted="currentITLMode == mode" 
                      @buttonClick="setITLMode(mode)">
          {{ mode }}
        </CustomButton>
      </div>
      <button v-if="currentITLMode != 'Idle'" class="rounded border border-red-800 bg-red-500 p-2 text-white w-full"
        @click="stop()">
        Stop
      </button>
    </div>
  </div>
</template>
<script setup lang="ts">
import { reactive, ref, watch, computed, onMounted } from "vue";
import { Furhat } from "furhat-gui";
import CustomButton from "./CustomButton.vue";

const modes: string[] = reactive(["LfD", "ITL"]);
const ITLModes = reactive(["Idle", "Learning", "Testing", "Evaluating"])
const currentMode = ref("");
const currentITLMode = ref("Idle");
let lastUpdate = 0;
const stale = ref(true);
setInterval(() => {
  stale.value = (new Date()).getTime() - lastUpdate > 2000;
}, 1000);

const participantId = ref("1");
const props = defineProps({
  furhat: {
    type: Furhat,
    required: true,
  }
})

const setMode = (mode: string) => {
  console.log("Setting mode to " + mode);
  props.furhat.send({"event_name": "GUIEvent", "type": "SetMode", "mode": mode, "participantId": participantId.value});
}

const setITLMode = (mode: string) => {
  props.furhat.send({"event_name": "GUIEvent", "type": "SetITLMode", "mode": mode});
}

const stop = () => {
  props.furhat.send({"event_name": "GUIEvent", "type": "StopLearning"});
}

onMounted(() => {
  console.log(props)
  console.log("Mounted");
  props.furhat.subscribe("furhatos.app.furhatdriver.ServerEvent", (data: any) => {
    if (data.type == "GUIState") {
      currentMode.value = data.mode;
      currentITLMode.value = data.ITLMode;
      participantId.value = data.participantId;
    } else if (data.type == "Heartbeat") {
      lastUpdate = (new Date()).getTime();
    }
  });
})

</script>
<style lang=""></style>
