package furhatos.app.furhatdriver.flow

import furhatos.app.furhatdriver.flow.main.Driver
import furhatos.app.furhatdriver.setting.distanceToEngage
import furhatos.app.furhatdriver.setting.maxNumberOfUsers
import furhatos.flow.kotlin.*
import furhatos.flow.kotlin.voice.PollyNeuralVoice

val Init : State = state() {
    init {
        /** Set our default interaction parameters */
        users.setSimpleEngagementPolicy(distanceToEngage, maxNumberOfUsers)
        furhat.voice = PollyNeuralVoice.Joanna().also { it.style = PollyNeuralVoice.Style.Conversational}

        /** start the interaction */
        goto(Driver)
    }
}
