"""
**********************************************
 FlyingCat 2015
 Under the BEER-WARE LICENSE
 google it for more details
**********************************************
"""

from XPLMDefs import *
from XPLMProcessing import *
from XPLMDataAccess import *
from XPLMUtilities import *
from XPLMPlanes import *
from XPLMPlugin import *
from XPLMMenus import *

YAK40 = 1
AN24RV = 2

# Using "displacement" axis function (See the Axis tab of Settnigs/Joystick and Equipment)
# 15 is just an offset in the drop down menu you use to assign the axis function
TURN_KNOB_AXIS = 15
MAX_AXIS_NUMBER = 100

class PythonInterface:
    def XPluginStart(self):
        self.Name = "APTurnKnob"
        self.Sig =  "FlyingCat"
        self.Desc = "Old style autopilot turn knob for AN24RV and YAK40 by Felis"

        self.interval = -1
        self.ap_turn_knob_axis = -1
        self.roll_com_DR = None
        self.acf_type = 0
        self.axis_values_DR = None
        self.axis_assignments_DR = None
        self.knob_state = False
        self.prev_knob_state = False
        
        self.ap_knob_toggle_CMD = XPLMCreateCommand("sim/autopilot/ap_turn_knob_toggle", "AN24_YAK40 turn knobe toggle");
        self.ap_knob_on_CMD = XPLMCreateCommand("sim/autopilot/ap_turn_knob_on", "AN24_YAK40 turn knob ON")
        self.ap_knob_off_CMD = XPLMCreateCommand("sim/autopilot/ap_turn_knob_off", "AN24_YAK40 turn knobe OFF")

        self.ap_knob_toggle_CH = self.ap_knob_toggle_command_handler
        self.ap_knob_on_CH = self.ap_knob_on_command_handler
        self.ap_knob_off_CH = self.ap_knob_off_command_handler
        XPLMRegisterCommandHandler(self, self.ap_knob_toggle_CMD, self.ap_knob_toggle_CH, 1, 0)        
        XPLMRegisterCommandHandler(self, self.ap_knob_on_CMD, self.ap_knob_on_CH, 1, 0)        
        XPLMRegisterCommandHandler(self, self.ap_knob_off_CMD, self.ap_knob_off_CH, 1, 0)        

        self.FlightLoopCB = self.FlightLoopCallback
        XPLMRegisterFlightLoopCallback(self, self.FlightLoopCB, self.interval, 0)
        return self.Name, self.Sig, self.Desc

    def ap_knob_toggle_command_handler(self, command, commandstate, refcon):
        if(commandstate == xplm_CommandBegin):
            if (self.knob_state == False):
                XPLMSpeakString("Turn knob enabled.")
                self.knob_state = True
            else:
                XPLMSpeakString("Turn knob disabled.")
                self.knob_state = False
        return 0

    def ap_knob_on_command_handler(self, command, commandstate, refcon):
        if(commandstate == xplm_CommandBegin):
            self.knob_state = True
        return 0

    def ap_knob_off_command_handler(self, command, commandstate, refcon):
        if(commandstate == xplm_CommandBegin):
            self.knob_state = False
        return 0

    def XPluginStop(self):
        # Unregister the callback
        XPLMUnregisterFlightLoopCallback(self, self.FlightLoopCB, 0)
        XPLMUnregisterCommandHandler(self, self.ap_knob_toggle_CMD, self.ap_knob_toggle_CH, 0, 0)
        XPLMUnregisterCommandHandler(self, self.ap_knob_on_CMD, self.ap_knob_on_CH, 0, 0)
        XPLMUnregisterCommandHandler(self, self.ap_knob_off_CMD, self.ap_knob_off_CH, 0, 0)
        pass

    def axis_and_aircraft_setup(self):
        assignments_values = []
        self.axis_values_DR = XPLMFindDataRef("sim/joystick/joystick_axis_values")
        self.axis_assignments_DR = XPLMFindDataRef("sim/joystick/joystick_axis_assignments")
        XPLMGetDatavi(self.axis_assignments_DR,assignments_values,0,MAX_AXIS_NUMBER)
        for i in range(MAX_AXIS_NUMBER):
            if assignments_values[i] == TURN_KNOB_AXIS:
                self.ap_turn_knob_axis = i
        #print "Axis for the old style autopilot turn knob: %d" % self.ap_turn_knob_axis    
        acf_descr = []
        XPLMGetDatab(XPLMFindDataRef("sim/aircraft/view/acf_descrip"),acf_descr,0,260)
        if acf_descr[0].find("Yak-40") != -1:
            self.acf_type = YAK40
        if acf_descr[0].find("An24RV") != -1:
            self.acf_type = AN24RV
        pass
    
    def XPluginEnable(self):
        self.axis_and_aircraft_setup()
        return 1

    def XPluginDisable(self):
        pass

    def XPluginReceiveMessage(self, inFromWho, inMessage, inParam):
        if (inFromWho == XPLM_PLUGIN_XPLANE):
            if (inParam == 0 and inMessage == XPLM_MSG_PLANE_LOADED):
                self.axis_and_aircraft_setup()
        pass

    def FlightLoopCallback(self, elapsedMe, elapsedSim, counter, refcon):
        axis_values = []
        if self.prev_knob_state != self.knob_state:
            if(self.roll_com_DR != None and self.knob_state == False):
                if self.acf_type == AN24RV:
                    XPLMSetDataf(self.roll_com_DR, 0.0)       
                if self.acf_type == YAK40:
                    XPLMSetDatai(self.roll_com_DR, 0)
        
        if self.knob_state == True:
            if(self.roll_com_DR == None):
                if self.acf_type == YAK40:
                    self.roll_com_DR = XPLMFindDataRef("sim/custom/xap/AP/roll_comm")
                if self.acf_type == AN24RV:
                    self.roll_com_DR = XPLMFindDataRef("sim/custom/xap/An24_ap/ap_roll")
    
            if self.ap_turn_knob_axis != -1 and self.roll_com_DR:
                XPLMGetDatavf(self.axis_values_DR, axis_values , 0 ,MAX_AXIS_NUMBER)   
                if self.acf_type == AN24RV:
                    rollf =  (axis_values[self.ap_turn_knob_axis]-0.5) * 60.0
                    XPLMSetDataf(self.roll_com_DR, rollf)       
                if self.acf_type == YAK40:
                    rolli =  int( (axis_values[self.ap_turn_knob_axis]-0.5) * 60.0)
                    XPLMSetDatai(self.roll_com_DR, rolli)
        self.prev_knob_state = self.knob_state            
        return self.interval


  

