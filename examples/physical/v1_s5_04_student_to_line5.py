"""V1-S5/T7-R1: verify Student -> autonomous Line5 ownership.

Supervised physical test only. Place robot on the line before starting.
Line5 lease is 120ms; 20ms repeated calls keep it refreshed.
"""
import rcu

rcu.SetMoveSpeed(60, 60)
rcu.SetWaitForTime(1)

for i in range(150):
    rcu.line_basis(70)
    rcu.SetWaitForTime(0.02)

rcu.SetMoveStop()
