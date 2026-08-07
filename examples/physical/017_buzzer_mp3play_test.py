import rcu


def task1():
  rcu.Set3CLed(1,3)
  rcu.Set3CLed(2,3)
  rcu.SetWaitForTime(5)
  rcu.SetMp3Play(1) 
  for i in range(5):
    rcu.SetMp3Play(1)
    wait(0.5)

task1()