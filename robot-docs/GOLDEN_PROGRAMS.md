# Golden Programs

This is the official regression suite for robot motion.

| Program | Description |
|---------|-------------|
| 001_forward.py | Move forward 1 sec at 50% speed |
| 002_backward.py | Move backward 1 sec at 50% speed |
| 003_turn_left.py | Turn left 1 sec at 50% speed |
| 004_turn_right.py | Turn right 1 sec at 50% speed |
| 005_square.py | Square pattern (4 forward/right) |
| 006_triangle.py | Triangle pattern |
| 007_circle_approx.py | Approximate circle |
| 008_zigzag.py | Zigzag pattern |

All programs use `SetMoveRunSecond` to ensure deterministic timing.