package furhatos.app.furhatdriver

import furhatos.app.furhatdriver.flow.*
import furhatos.skills.Skill
import furhatos.flow.kotlin.*
import furhatos.skills.HostedGUI

class FurhatDriverSkill : Skill() {
    val api = HostedGUI("MyRemoteGUI", "assets/wizard-gui/dist", port = 1234)

    override fun start() {
        Flow().run(Init)
    }
}

fun main(args: Array<String>) {
    Skill.main(args)
}
