import rcu


def task1():
  while True:
    if (rcu.GetTouch(1)):
      rcu.SetMoveSpeed(50, 50)

task1()