package furhatos.app.furhatdriver.flow.main

import furhatos.event.Event
import furhatos.flow.kotlin.*
import furhatos.records.User


val Driver: State = state {
    var infinite: Boolean = false
    onEntry {
//        furhat.attendAll()
        furhat.param.endSilTimeout = 500
        furhat.param.noSpeechTimeout = 8000
        furhat.param.maxSpeechTimeout = 60000
        dialogLogger.startSession(maxLength = 6000, cloudToken = "0cb0c591-7781-47bb-8417-6a4fe3993c05")
    }
//
    onExit {
        dialogLogger.endSession()
    }
//
    onInterimResponse {
        furhat.attend(user = User(it.speech.userId))
    }

    onResponse {
        dialogLogger.logInfo("response")
        furhat.attend(user = User(it.userId))
        if (infinite) {
            furhat.listen()
        }
    }
//
    onResponseFailed {
        dialogLogger.logInfo("ASR failure at time " + it.time)
        if (infinite) {
            furhat.listen()
        }
    }
//
    onNoResponse {
//        furhat.attendAll()
        if (infinite) {
            furhat.listen()
        }
    }

    onEvent("GUIEvent") {
        dialogLogger.logInfo(it.eventParams.toString())
        send("furhatos.app.furhatdriver.GUIEvent", it.eventParams.toMap())
    }

    onEvent("ServerEvent") {
        if (it.getString("type") != "Heartbeat") {
            dialogLogger.logInfo(it.eventParams.toString())
        }
        send("furhatos.app.furhatdriver.ServerEvent", it.eventParams.toMap())
    }

    onEvent("furhatos.app.furhatdriver.CustomListen") {
        furhat.stopListening()
        infinite = it.getBoolean("infinite", false)
        furhat.param.endSilTimeout = it.getInteger("endSilTimeout", 1000)
        furhat.param.noSpeechTimeout = it.getInteger("timeout", 10000)
        furhat.listen()
    }

    onEvent("furhatos.app.furhatdriver.StopListen") {
        infinite = false
        furhat.stopListening()
    }

}
