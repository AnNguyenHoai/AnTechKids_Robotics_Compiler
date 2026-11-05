import rcu

VAR_Sen2 = 0
VAR_Sen3 = 0
VAR_Sen4 = 0
VAR_Sen6 = 0
VAR_Sen5 = 0
VAR_Sen1 = 0
VAR_Sen7 = 0

def DiChuyen():
    global VAR_Sen2, VAR_Sen3, VAR_Sen4, VAR_Sen6, VAR_Sen5
    if VAR_Sen6 == 1:
        rcu.SetMoveSpeed(70, 0)
    else:
        if VAR_Sen5 == 1:
            rcu.SetMoveSpeed(70, 40)
        else:
            if VAR_Sen4 == 1:
                rcu.SetMoveSpeed(70, 70)
            else:
                if VAR_Sen3 == 1:
                    rcu.SetMoveSpeed(40, 70)
                else:
                    if VAR_Sen2 == 1:
                        rcu.SetMoveSpeed(0, 70)
                    else:
                        pass

def DocCamBiet():
    global VAR_Sen2, VAR_Sen3, VAR_Sen4, VAR_Sen6, VAR_Sen5, VAR_Sen1, VAR_Sen7
    VAR_Sen1 = rcu.GetTraceV2I2CState(1, 1)
    VAR_Sen2 = rcu.GetTraceV2I2CState(1, 2)
    VAR_Sen3 = rcu.GetTraceV2I2CState(1, 3)
    VAR_Sen4 = rcu.GetTraceV2I2CState(1, 4)
    VAR_Sen5 = rcu.GetTraceV2I2CState(1, 5)
    VAR_Sen6 = rcu.GetTraceV2I2CState(1, 6)
    VAR_Sen7 = rcu.GetTraceV2I2CState(1, 7)

def task1():
    global VAR_Sen2, VAR_Sen3, VAR_Sen4, VAR_Sen6, VAR_Sen5
    rcu.SetMoveSpeed(50, 50)
    rcu.SetWaitForTime(0.5)
    while True:
        DocCamBiet()
        if (VAR_Sen2 == 1 and VAR_Sen3 == 1) and VAR_Sen4 == 1:
            rcu.SetMoveSpeed(-70, 70)
        else:
            if (VAR_Sen6 == 1 and VAR_Sen5 == 1) and VAR_Sen4 == 1:
                rcu.SetMoveSpeed(70, -70)
            else:
                if VAR_Sen2 == 1 and VAR_Sen4 == 1:
                    rcu.SetMoveSpeed(-70, 70)
                else:
                    if VAR_Sen4 == 1 and VAR_Sen6 == 1:
                        rcu.SetMoveSpeed(70, -70)
                    else:
                        if VAR_Sen3 == 1 and VAR_Sen4 == 1:
                            rcu.SetMoveSpeed(-70, 70)
                        else:
                            if VAR_Sen4 == 1 and VAR_Sen5 == 1:
                                rcu.SetMoveSpeed(70, -70)
                            else:
                                DiChuyen()
        rcu.SetWaitForTime(0.02)
task1()
