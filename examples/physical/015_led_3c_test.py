import rcu


def task1():
  rcu.Set3CLed(1,3)
  rcu.SetWaitForTime(1)

task1()