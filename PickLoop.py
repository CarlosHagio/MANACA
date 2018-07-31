#################################################################
#   DESCRIPTION: PV's manipulator script for 1DT operation mode #
#   (loop manipulator)                                          #              
#                                                               #
#   FUTURE IMPROVEMENTS: implement auxiliar functions file,     #
#   common to all other operations modes.                       #  
#                                                               #
#   LAST MODIFICATION: Carlos (31/7) - added waitEndMove        #
#   and auxStopMovei. Detached tool's action from robot         #
#   movements.                                                  #
#################################################################

from epics import PV, camonitor
import time

#############################################
#  PV's definition                          #
#                                           #         
#  Object oriented approach                 #
#                                           #
#  Carlos (27/7): creation:                 #
#   PV's are global.                        #
#                                           #
#   pvPower: turn robot power on/off (1/0)  #
#                                           #
#   pvSetFrame: define cartesian frame for  #
#       comands bellow                      #
#                                           #
#   pvGetX/Y/Z: get robot tool position,    #
#       must be aware of which frame is on  #
#                                           #
#   pvMoveX/Y/Z: move robot in cartesian    #
#        directions, frame must be known    #
#                                           #
#   pvPickLoop: get loop from dewar and     #
#       wait in dewar frame reference       #
#       position                            #
#                                           #
#   pvRetrieveLoop: return loop from beam   #
#       position to dewar                   #
#                                           #
#   pvPlaceLoop: takes loop from dewar      #
#       reference to beam position          # 
#                                           #   
#   pvStopMove: interrupt and store robot   #
#       movement                            #
#                                           #
#   pvDeleteMove: delete movement stack     #
#                                           #
#   pvRestartMove: restart movements in     # 
#       stack                               #
#                                           #
#   pvCheckMoving: feedbacks robot          # 
#       condition (moving-1 or not-0)       #
#                                           #
#   pvSetTool: defines robot tool in        #
#       controller (hard coded-just use     #
#       it in development)                  #
#                                           #
#   pvPickTool: changes robot tool (proper  #
#       way)                                #
#                                           #
#   pvGripper: open/close robot tool (0/1)  #
#                                           #
#############################################

pvPower, pvPickLoop, pvPlaceLoop, pvRetrieveLoop, pvGripper, pvCheckMoving, pvStopMove = (None,)*7

def definePVs():
    global pvPower, pvPickLoop, pvPlaceLoop, pvRetrieveLoop, pvGripper, pvCheckMoving, pvStopMove
    
    pvPower = PV('MXROB:Staubli2:Power.VAL')
    
    pvGetX = PV('MXROB:Staubli2:GetX.VAL')
    pvGetY = PV('MXROB:Staubli2:GetY.VAL')
    pvGetZ = PV('MXROB:Staubli2:GetZ.VAL')

    pvMoveX = PV('MXROB:Staubli2:MoveX.VAL')
    pvMoveY = PV('MXROB:Staubli2:MoveY.VAL')
    pvMoveZ = PV('MXROB:Staubli2:MoveZ.VAL')

    pvPickLoop = PV('MXROB:Staubli2:PickLoop.VAL')
    pvRetrieveLoop = PV('MXROB:Staubli2:RetrieveLoop.VAL')
    pvPlaceLoop = PV('MXROB:Staubli2:PlaceLoop.VAL')

    pvStopMove = PV('MXROB:Staubli2:StopMove.VAL')
    pvDeleteMove = PV('MXROB:Staubli2:DeleteMove.VAL')
    pvRestartMove = PV('MXROB:Staubli2:RestartMove.VAL')
    pvCheckMoving = PV('MXROB:Staubli2:CheckMoving.VAL')

    pvSetTool = PV('MXROB:Staubli2:SetTool.VAL')
    pvPickTool = PV('MXROB:Staubli2:PickTool.VAL')
    pvGripper = PV('MXROB:Staubli2:Gripper.VAL')

    return

#############################################
#                                           #
#   End PV's definition                     #
#                                           #
#############################################

################################################################

#################################################
#                                               #
#   Take dewar's loops:                         #
#                                               #
#   Take from dewar to beam and back            # 
#   argument is the loop index nLoop            #
#                                               #
#   Carlos (31/7): added waitEndMove to work    #
#   with user interference                      # 
#                                               #
#################################################
def pickLoop(nLoop):
    print("\n\nbegin")
    print("pick loop ", nLoop)    
    pvPickLoop.put(nLoop, wait = True)
    waitEndMove()    
    
    print("close gripper")
    pvGripper.put(0, wait = True)
    time.sleep(0.5)

    print("place loop ", nLoop)
    pvPlaceLoop.put(0, wait = True)
    waitEndMove()

    print("retrieve loop ", nLoop)
    pvRetrieveLoop.put(nLoop, wait = True)
    waitEndMove()
    
    print("open gripper")
    pvGripper.put(1, wait = True)
    
    print("end\n\n")

#############################################
#                                           #
#   End pickLoop                            #
#                                           #
#############################################


######################################################
#############################################
#                                           #
#   Called when user inputs PV StopMove 0,  #
#   holds until user enable movement again  #
#   using PV StopMove 1                     #
#                                           #
#   Carlos(31/7): creation                  #
#                                           #
#############################################
def auxStopMove():
    print("auxStopMove: ", pvStopMove.get())
    while(pvStopMove.get()==1):
        print("stopped")
        time.sleep(1)
#############################################
#                                           #
#   End auxStopMove                         #
#                                           #
#############################################

#############################################
#   Hold the program execution until arm    #
#   movement ends.                          #
#   Called when script inputs 1DT related   #
#   movements. It turned up necessary       #
#   because the gripper commands,           #
#   intercalated with robot movements,      #
#   blocks IOC and robot communication      #
#                                           #
#   Carlos (31/7): creation                 #
#############################################
def waitEndMove():
    print("wait end move")
    while(pvCheckMoving.get()==0):
        print("not moving")
        if(pvStopMove.get() == 1):
            auxStopMove()
        pass
    while(pvCheckMoving.get()==1):
        print("moving")
        if(pvStopMove.get()==1):
            auxStopMove()
        pass
    print("finished")
#############################################
#                                           #
#   End waitEndMove                         #
#                                           #
#############################################



#####################################################

#################################################
#                                               #
#   if for direct usage (i.e. debugging)        #
#   Turns arm power ON. Pick every single loop  #
#   from the dewar to the beam and back. Turns  #
#   arm power OFF.                              #
#                                               #
#   else for using elsewhere (i.e. integrating  # 
#   with others scripts).                       #        
#                                               #
#   Carlos (31/7): reorganization (explicitly   # 
#   calling pvPower, which was called by        #
#   pickloop before).                           #
#                                               #
#################################################
if __name__ == "__main__":
    
    definePVs()
    pvPower.put(1, wait = True)
    for nLoop in range (1, 5) :
        pickLoop(nLoop)
    pvPower.put(0, wait = True)
else:
    print("importing PickLoop.py")

