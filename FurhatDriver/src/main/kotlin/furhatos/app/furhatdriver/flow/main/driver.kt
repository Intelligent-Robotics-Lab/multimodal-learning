package furhatos.app.furhatdriver.flow.main

import furhatos.event.Event
import furhatos.event.monitors.MonitorSpeechStart
import furhatos.flow.kotlin.*
import furhatos.flow.kotlin.voice.AzureVoice
import furhatos.records.Location
import furhatos.records.User
import furhatos.util.CommonUtils
import furhatos.util.Language

val Background: State = state {
    onEvent("GUIEvent", instant = true) {
//        dialogLogger.logInfo(it.eventParams.toString())
        send("furhatos.app.furhatdriver.GUIEvent", it.eventParams.toMap())
    }
//
    onEvent("ServerEvent", instant = true) {
        send("furhatos.app.furhatdriver.ServerEvent", it.eventParams.toMap())
    }
}

val Driver: State = state {
    var infinite: Boolean = false
    onEntry {
        furhat.attendAll()
        println("Entry")
        furhat.param.endSilTimeout = 1000
        furhat.param.noSpeechTimeout = 8000
        furhat.param.maxSpeechTimeout = 60000
//        dialogLogger.startSession(maxLength = 6000, cloudToken = "0cb0c591-7781-47bb-8417-6a4fe3993c05")
        parallel(Background)
    }

    onUserEnter(instant = true) {
        if (furhat.users.count > 1) {
            furhat.attendAll()
        } else {
            furhat.attend(it)
        }
    }

    onUserLeave(instant = true) {
        if (furhat.users.count == 0) {
            furhat.attendNobody()
        } else {
            furhat.attend(furhat.users.userClosestToPosition(Location(0,0,2)))
        }
    }
//
    onExit {
//        dialogLogger.endSession()
    }

    onInterimResponse {
        furhat.attend(user = User(it.speech.userId))
    }

    onResponse {
        println("Response: " + it.text)
        if (infinite) {
            furhat.listen()
        }
    }
//
    onResponseFailed {
        println("Response failed")
//        dialogLogger.logInfo("ASR failure at time " + it.time)
        furhat.listen()
    }
//
    onNoResponse {
        furhat.attendAll()
        println("No response")
        if (infinite) {
            furhat.listen()
        }
    }

    onEvent<MonitorSpeechStart>(instant = true) {
        furhat.attend(furhat.users.current)
    }

    onEvent("furhatos.app.furhatdriver.CustomListen") {
        furhat.stopListening()
        infinite = it.getBoolean("infinite", false)
        furhat.param.endSilTimeout = it.getInteger("endSilTimeout", 1000)
        furhat.param.noSpeechTimeout = it.getInteger("noSpeechTimeout", 10000)
        println("Listening")
        furhat.listen()
    }
//
    onEvent("furhatos.app.furhatdriver.StopListen") {
        infinite = false
        furhat.stopListening()
        furhat.attendAll()
    }

}
