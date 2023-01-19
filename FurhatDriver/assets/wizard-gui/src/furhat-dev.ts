import Furhat from 'furhat-core'
import type { Event, EventCallback } from 'furhat-core'

let furhat: Furhat
let portNumber: string

const FurhatGUI: () => Promise<Furhat> = () => new Promise((resolve, reject) => {
    Promise.resolve() // eslint-disable-line no-undef
      .then(() => {
        portNumber = "8080"
        furhat = new Furhat("0.0.0.0", 8080, 'api')
        return furhat.init()
      })
      .then(() => {
        const senseSkillGuiEvent: Event = {
          event_name: 'furhatos.event.senses.SenseSkillGUIConnected',
          port: portNumber,
        }
        furhat.send(senseSkillGuiEvent)
        resolve(furhat)
      })
      .catch((error) => reject(`Something went wrong: ${error}`))
  })

  export default FurhatGUI