import rcu

VAR_distance = 0

def task1():
  global VAR_distance
  VAR_distance = rcu.GetUltrasound(1)
  if (VAR_distance < 20):
    rcu.SetMoveRunSecond("forward", 50, 1)
  else:
    rcu.SetMoveRunSecond("backward", 50, 1)

task1()