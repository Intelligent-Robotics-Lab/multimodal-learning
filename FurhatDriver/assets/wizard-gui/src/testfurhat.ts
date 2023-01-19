import FurhatGUI, { Furhat } from "furhat-gui";
// import WebSocket from 'ws';
let furhat: Furhat;

function setupSubscriptions() {
  furhat.subscribe("com.myapp.MyCustomEvent", (event) => {
    console.log("received event: ", event.event_name);
  });
}
let socket = new WebSocket("localhost:8080");
socket.onerror
FurhatGUI()
  .then((connection) => {
    furhat = connection;
    furhat.onConnectionError((ev: Event) => {});
    furhat.onConnectionClose(() => {
      console.warn("Connection with Furhat skill has been closed");
    });
    setupSubscriptions();
  })
  .catch(console.error);