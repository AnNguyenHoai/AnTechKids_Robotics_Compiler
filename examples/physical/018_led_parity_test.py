import rcu

# P1 -> GPIO33, P2 -> GPIO32, P3 -> GPIO33, P4 -> GPIO32
rcu.Set3CLed(1, 1)   # GPIO33 ON
rcu.SetWaitForTime(0.5)
rcu.Set3CLed(1, 0)   # GPIO33 OFF
rcu.SetWaitForTime(0.5)
rcu.Set3CLed(2, 1)   # GPIO32 ON
rcu.SetWaitForTime(0.5)
rcu.Set3CLed(2, 0)
rcu.SetWaitForTime(0.5)
rcu.Set3CLed(3, 1)   # GPIO33 ON
rcu.SetWaitForTime(0.5)
rcu.Set3CLed(3, 0)
rcu.SetWaitForTime(0.5)
rcu.Set3CLed(4, 1)   # GPIO32 ON
rcu.SetWaitForTime(0.5)
rcu.Set3CLed(4, 0)