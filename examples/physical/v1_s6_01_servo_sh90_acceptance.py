"""V1-S6 supervised SH90 acceptance. Servo selected, Buzzer disabled on GPIO19.
WARNING: Remove gripper linkage for first run; bench supply and shared GND required.
"""
import rcu

# Neutral, then gentle movement within initially conservative test angles.
rcu.SetServo(1, 90)
rcu.SetWaitForTime(2)
rcu.SetServo(1, 70)
rcu.SetWaitForTime(2)
rcu.SetServo(1, 110)
rcu.SetWaitForTime(2)
rcu.SetServo(1, 90)
rcu.SetWaitForTime(1)
