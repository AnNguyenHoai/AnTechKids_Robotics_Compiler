# Sprint S3.2 --- RoboSim API Interface Inventory & Canonical Contract

**Assignee:** DeepSeek\
**Epic:** RoboSim Compatibility\
**Milestone:** RC1 --- Interface Coverage\
**Priority:** Critical\
**Type:** Inventory / Interface Architecture / Contract\
**Prerequisite:** S3.1A + S3.1A.1 CLOSED\
**S3.1B:** PAUSED --- behavioral semantics will be resumed during
physical implementation

------------------------------------------------------------------------

# 1. Objective

Build the master inventory of RoboSim APIs actually used by available
RoboSim samples/code and define the canonical interface contract
required to carry those APIs toward RobotAPI.

The new project goal is:

``` text
RoboSim API
    ↓
RoboSim Adapter
    ↓
Canonical Robot Language API
    ↓
Compiler
    ↓
Bytecode
    ↓
VM
    ↓
RobotAPI interface
    ↓
REAL or DUMMY implementation
```

This sprint does **not** implement the full pipeline.

It establishes the complete interface surface and the implementation
plan for subsequent coverage sprints.

------------------------------------------------------------------------

# 2. Strategic Change

Previously, unknown RoboSim semantics blocked creation of an
implementation contract.

For the Interface Coverage milestone, this rule changes:

``` text
Unknown physical semantics
        ≠
Cannot define transport interface
```

We may define an interface when we know the observable RoboSim call
signature sufficiently to preserve:

``` text
API name
argument count
argument order
literal/value types
return-value usage
```

However:

``` text
UNKNOWN semantics
```

must never be represented as:

``` text
PHYSICAL_IMPLEMENTED
FULL COMPATIBILITY
```

Unknown behavior will terminate at a RobotAPI dummy implementation in
later sprints.

------------------------------------------------------------------------

# 3. Primary Task --- Discover RoboSim API Surface

Search all available project sources for RoboSim calls, especially:

``` text
examples/
tests/
goldens/
fixtures/
sample programs/
RoboSim generated Python
existing docs/specs
frontend transformer tests
```

Collect every unique call matching patterns such as:

``` python
rcu.*
```

Also inventory relevant non-`rcu` runtime dependencies used by generated
RoboSim code, such as:

``` python
_thread.start_new_thread(...)
```

but classify runtime/language features separately.

Do not limit inventory to the current RC1 acceptance program.

------------------------------------------------------------------------

# 4. API Categories

Classify discovered APIs into at least:

``` text
MOTION
SENSOR_LIGHT
SENSOR_ULTRASONIC
SENSOR_TOUCH
PATROL_LINE
LINE_BEHAVIOR
LED
BUZZER / SOUND
SERVO
DISPLAY
SYSTEM / UTILITY
OTHER
```

Runtime constructs must use separate categories:

``` text
RUNTIME
LANGUAGE_FEATURE
```

Examples:

``` text
_thread.start_new_thread → RUNTIME
while                   → LANGUAGE_FEATURE
break                    → LANGUAGE_FEATURE
```

------------------------------------------------------------------------

# 5. Master Inventory

Create:

``` text
robot-docs/robosim/ROBOSIM_API_MASTER_INVENTORY.md
```

Required table:

  -------------------------------------------------------------------------------------------------------
  RoboSim   Category   Observed    Return   Evidence   Current   Compiler   VM      RobotAPI   Physical
  API                  Signature   Used?    Source     Adapter                                 
  --------- ---------- ----------- -------- ---------- --------- ---------- ------- ---------- ----------

  -------------------------------------------------------------------------------------------------------

Use status values:

``` text
YES
NO
PARTIAL
UNKNOWN
N/A
```

For physical implementation use:

``` text
REAL
DUMMY
MISSING
UNKNOWN
N/A
```

Do not mark physical support based only on software support.

------------------------------------------------------------------------

# 6. Evidence Per API

For each API record at least one concrete evidence location:

``` text
file
sample
test
spec
generated program
```

Example:

``` text
API: SetMoveSpeed
Evidence:
- examples/...
- frontend test ...
Observed call:
rcu.SetMoveSpeed(-50, 70)
```

Do not add speculative APIs merely because they sound plausible.

If an existing RoboSim specification contains APIs not yet observed in
samples, place them in a separate:

``` text
SPEC_ONLY
```

section.

------------------------------------------------------------------------

# 7. Signature Preservation

For every observed API determine what can be established without
guessing semantics:

``` text
argument count
argument ordering
observed literal types
whether return value is used
whether call appears in condition/expression
```

Example:

``` python
rcu.GetTraceV2I2C(1, 1) == 50
```

establishes:

``` text
argument count = 2
return value exists
return participates in numeric comparison
```

It does NOT establish what the returned number physically means.

Preserve that distinction.

------------------------------------------------------------------------

# 8. Canonical Interface Design

Create:

``` text
robot-docs/robosim/ROBOSIM_CANONICAL_INTERFACE_CONTRACT.md
```

Define a canonical Robot Language interface for each RoboSim API that
should cross the Robot Platform boundary.

Example pattern:

``` text
RoboSim:
rcu.SetMoveSpeed(left, right)

Canonical:
set_motor_speed(left, right)
```

For unresolved APIs, a transport interface is still allowed:

``` text
RoboSim:
rcu.GetTraceV2I2C(port, arg)

Canonical:
get_trace_v2_i2c(port, arg)
```

Do not reinterpret `arg` if its semantics are unknown.

Prefer preserving unknown parameters over inventing names such as:

``` text
threshold
channel
position
```

without evidence.

------------------------------------------------------------------------

# 9. Canonical Naming Rules

Canonical names should be:

``` text
snake_case
platform-oriented
stable
one semantic operation per function
```

Prefer:

``` text
get_trace_v2_i2c(...)
line_basis(...)
move_run_angle(...)
```

over aggressively translating unknown behavior into a guessed generic
primitive.

For already established canonical APIs, preserve current names unless
there is a strong architecture reason to change them.

Avoid unnecessary breaking changes.

------------------------------------------------------------------------

# 10. Return Contract

For every canonical API classify:

``` text
COMMAND
QUERY
```

## COMMAND

Example:

``` text
set_motor_speed(...)
```

Expected return:

``` text
void / none
```

## QUERY

Example:

``` text
get_trace_v2_i2c(...)
```

Must preserve a return path through:

``` text
RobotAPI
→ VM value
→ program variable/expression
```

If exact return type is unknown but observed code performs:

``` text
== 50
```

classify conservatively as:

``` text
numeric-compatible return
```

Do not invent a physical range.

------------------------------------------------------------------------

# 11. Support State Model

Replace ambiguous single compatibility status with explicit layers.

For each API track:

``` text
INTERFACE_DEFINED
ADAPTER_SUPPORTED
COMPILER_SUPPORTED
VM_SUPPORTED
ROBOT_API_SUPPORTED
IMPLEMENTATION_STATE
```

`IMPLEMENTATION_STATE` must be one of:

``` text
REAL
DUMMY
MISSING
N/A
```

Optional semantic state:

``` text
KNOWN
PARTIAL
UNKNOWN
```

Example:

``` text
line_basis

Interface       DEFINED
Adapter         MISSING
Compiler        MISSING
VM              MISSING
RobotAPI        MISSING
Implementation  MISSING
Semantics       UNKNOWN
```

Future state may become:

``` text
Interface       DEFINED
Adapter         YES
Compiler        YES
VM              YES
RobotAPI        YES
Implementation  DUMMY
Semantics       UNKNOWN
```

This is valid for the Interface Coverage milestone.

------------------------------------------------------------------------

# 12. RobotAPI Target Surface

Design the target RobotAPI declarations needed for the discovered
RoboSim interface surface.

Create:

``` text
robot-docs/robosim/ROBOT_API_TARGET_SURFACE.md
```

For each API show the proposed declaration.

Example:

``` cpp
void SetMotorSpeed(int left, int right);

int GetTraceV2I2C(int port, int arg);

void LineBasis(int speed);
```

If a type is not established, use the narrowest safe representation
consistent with observed code and explicitly mark:

``` text
TYPE CONTRACT PROVISIONAL
```

Do not implement these functions in S3.2.

------------------------------------------------------------------------

# 13. Dummy Boundary Contract

Document the future dummy rule:

``` text
Adapter
Compiler
VM
RobotAPI declaration
```

must be real infrastructure.

Only the implementation behind RobotAPI may be dummy.

Allowed future pattern:

``` cpp
int GetTraceV2I2C(int port, int arg) {
    Serial.printf(
        "[DUMMY] GetTraceV2I2C port=%d arg=%d\n",
        port,
        arg
    );
    return 0;
}
```

Forbidden patterns:

``` text
Transformer deletes the call
Compiler ignores the call
VM treats opcode as NOP
Return query has no value path
```

Dummy query APIs must return a deterministic placeholder value and
clearly log that they are dummy.

Exact dummy values will be defined during implementation sprint, not
guessed here.

------------------------------------------------------------------------

# 14. Runtime Features

Create a separate section for constructs such as:

``` text
_thread.start_new_thread
while True
while 1
function definitions
function calls
global
nested if
break
continue
```

Do not map these to RobotAPI.

Classify each as:

``` text
Compiler language support
VM runtime support
Scheduler requirement
```

This will become input for a later runtime sprint.

------------------------------------------------------------------------

# 15. Existing Real APIs

Identify APIs already backed by real hardware implementations.

Expected examples may include:

``` text
SetMoveSpeed
SetMoveRunSecond
Ultrasonic
Touch
Light
Line channel read
```

Verify against source rather than assuming.

These must remain:

``` text
IMPLEMENTATION_STATE = REAL
```

Do not replace existing real implementations with dummy functions.

------------------------------------------------------------------------

# 16. API Coverage Metrics

Create baseline metrics:

``` text
Total observed RoboSim APIs
Interface-defined APIs
Adapter-supported APIs
Compiler-supported APIs
VM-supported APIs
RobotAPI-supported APIs
REAL implementations
DUMMY implementations
MISSING implementations
```

Calculate:

``` text
Interface Coverage %
Adapter Coverage %
Compiler Coverage %
VM Dispatch Coverage %
RobotAPI Surface Coverage %
```

Do NOT calculate a misleading physical compatibility percentage for
unknown/dummy APIs.

------------------------------------------------------------------------

# 17. Prioritization

Create:

``` text
robot-docs/robosim/ROBOSIM_INTERFACE_COVERAGE_BACKLOG.md
```

Prioritize APIs using actual sample frequency and dependency.

Suggested levels:

``` text
P0 — blocks many RoboSim samples
P1 — common
P2 — less common
P3 — spec-only / no observed usage
```

Also identify dependency groups.

Example:

``` text
line_* APIs
    depend on
query/value transport
    + command transport
```

Do not prioritize only by ease of implementation.

------------------------------------------------------------------------

# 18. Next Sprint Decomposition

At the end of the backlog, propose implementation batches.

Target direction:

``` text
S3.3A — Motion interfaces
S3.3B — Sensor query interfaces
S3.3C — Patrol/Line interfaces
S3.3D — Other RoboSim peripheral interfaces
```

or a better decomposition based on actual inventory evidence.

Each batch should be small enough for independent review.

Do not automatically implement them.

------------------------------------------------------------------------

# 19. Documentation Cleanup

Correct stale time-unit statements in:

``` text
robot-docs/TIMING_AUDIT.md
robot-docs/PHYSICAL_TOOLCHAIN_VALIDATION.md
```

Frozen contract:

``` text
RoboSim time APIs = seconds
Canonical wait    = milliseconds
VM/Firmware wait  = milliseconds
```

This cleanup is allowed in S3.2.

------------------------------------------------------------------------

# 20. Deliverables

Required:

``` text
robot-docs/robosim/
├── ROBOSIM_API_MASTER_INVENTORY.md
├── ROBOSIM_CANONICAL_INTERFACE_CONTRACT.md
├── ROBOT_API_TARGET_SURFACE.md
└── ROBOSIM_INTERFACE_COVERAGE_BACKLOG.md
```

Also provide:

``` text
S3_2_INVENTORY_REPORT.md
```

containing:

``` text
files searched
number of APIs discovered
coverage baseline
major unsupported groups
runtime gaps
recommended implementation order
```

------------------------------------------------------------------------

# 21. Non-Goals

Do NOT:

``` text
add new opcodes
modify VM dispatch
implement RobotAPI dummy functions
implement line behavior
implement sensor semantics
implement _thread scheduler
fake physical compatibility
rewrite working real APIs
```

This sprint defines the surface before implementation.

------------------------------------------------------------------------

# 22. Acceptance Criteria

S3.2 PASS requires:

-   [ ] All available RoboSim samples/tests are searched.
-   [ ] Every observed `rcu.*` API is inventoried.
-   [ ] Evidence source exists for every observed API.
-   [ ] SPEC_ONLY APIs are separated from observed APIs.
-   [ ] Runtime/language features are separated from RobotAPI APIs.
-   [ ] Argument count/order and return usage are captured.
-   [ ] Unknown parameter semantics remain unknown.
-   [ ] Canonical interface exists for every target observed API.
-   [ ] COMMAND vs QUERY is classified.
-   [ ] RobotAPI target surface is defined.
-   [ ] REAL/DUMMY/MISSING state model is documented.
-   [ ] Existing real hardware APIs remain REAL.
-   [ ] Baseline coverage metrics are calculated.
-   [ ] Implementation backlog is prioritized from evidence.
-   [ ] Subsequent implementation batches are proposed.
-   [ ] Time-unit documentation debt is corrected.
-   [ ] No new compatibility implementation is introduced.

------------------------------------------------------------------------

# 23. Review Gate

``` text
S3.2 Inventory
      ↓
Architecture Review
      ↓
Master Interface Surface accepted?
      ├── NO → revise inventory/contract
      └── YES
             ↓
Interface Contract baseline frozen
             ↓
S3.3 implementation batches
```

DeepSeek must not begin S3.3 automatically.

------------------------------------------------------------------------

# Definition of Done

The project has one evidence-backed master answer to:

> Which RoboSim APIs do our available programs actually use, what
> call/return interface must the Robot Platform preserve for each one,
> which layers already support them, and which interfaces must be
> implemented next so RoboSim programs can compile and dispatch all the
> way to RobotAPI even when physical behavior remains dummy?
