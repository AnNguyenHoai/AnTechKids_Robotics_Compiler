import rcu


def task1():
  rcu.Set3CLed(1,3)
  rcu.Set3CLed(2,3)
  rcu.SetWaitForTime(5)
  rcu.SetMp3Play(1) 
  rcu.SetMoveRunSecond("forward", 80, 10)

task1()