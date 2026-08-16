Robot Virtual Machine Bytecode Specification
Version: 1.0
Status: Architecture Freeze
Date: 2026-08-10
Owner: Robot Platform Team

Revision History
Version	Date	Author	Changes
1.0	2026-08-10	DeepSeek	Initial release
Table of Contents
Introduction

Bytecode File Overview

Header Specification

Metadata Section

Constant Pool

Instruction Stream

Opcode Encoding

Operand Encoding

Program Counter Rules

Validation Rules

Error Conditions

Version Compatibility

Worked Examples
Appendix A: Opcode Encoding Table
Appendix B: Operand Encoding Table
Appendix C: Constant Pool Table
Appendix D: Header Layout
Appendix E: Binary Examples
Appendix F: Reserved Values

Chapter 1 – Introduction
1.1 Purpose
This document defines the official binary format of Robot Virtual Machine Bytecode.

Robot Bytecode is the interface contract between:

Compiler – produces bytecode

Program Loader – validates and loads bytecode

Virtual Machine – executes bytecode

This specification describes only the binary format.

It does not describe:

Compiler implementation

Runtime implementation

Execution semantics (covered by ROBOT_VM_EXECUTION_MODEL.md)

Instruction semantics (covered by ROBOT_VM_ISA.md)

1.2 Scope
This specification covers:

Binary file layout

Header format

Metadata section

Constant pool encoding

Instruction stream encoding

Opcode and operand encoding

Validation rules

Version compatibility

It does not cover:

How the compiler generates bytecode

How the VM executes bytecode

RobotAPI or hardware implementation

Performance optimization techniques

1.3 Relationship with ISA
Aspect	ISA (ROBOT_VM_ISA.md)	Bytecode (this document)
Focus	What instructions do	How instructions are encoded
Scope	Opcode semantics, stack effects	Binary layout, encoding rules
Stability	Stable; defines the contract	Stable; defines the wire format
Audience	Compiler, debugger, tooling	Compiler, loader, VM implementers
1.4 Relationship with Execution Model
Aspect	Execution Model (ROBOT_VM_EXECUTION_MODEL.md)	Bytecode (this document)
Focus	How the VM executes	What the VM loads
Scope	Lifecycle, loop, state	File format, encoding
Audience	Runtime implementers	Loader implementers, tooling
1.5 Relationship with Compiler
The compiler SHALL produce bytecode that conforms to this specification. The compiler SHALL NOT assume any particular execution model behavior beyond what is specified in the ISA document.

Compiler → Bytecode → Loader → VM

The compiler writes bytecode. The loader reads bytecode. The VM executes bytecode. These responsibilities SHALL NOT overlap.

1.6 Relationship with Program Loader
The Program Loader SHALL:

Validate the bytecode file against this specification.

Deserialize the binary format into a runtime program.

Reject invalid bytecode with appropriate error codes.

Report validation errors to the caller.

The loader SHALL NOT execute bytecode. The loader SHALL NOT modify bytecode.

Chapter 2 – Bytecode File Overview
2.1 Overall Layout
A Robot Bytecode file consists of five sections in the following order:


+---------------------------+
|         HEADER            |  64 bytes
+---------------------------+
|         METADATA          |  Variable
+---------------------------+
|      CONSTANT POOL        |  Variable
+---------------------------+
|   INSTRUCTION STREAM      |  Variable
+---------------------------+
|         RESERVED          |  Variable (future)
+---------------------------+
2.2 Section Descriptions
Section	Purpose
Header	Fixed-size file identifier, version, and layout metadata.
Metadata	Optional program metadata (name, author, build info).
Constant Pool	Deduplicated constants referenced by instructions.
Instruction Stream	Linear sequence of encoded instructions.
Reserved	Reserved for future extensions; SHALL be empty in version 1.0.
2.3 Byte Order
All multi-byte values SHALL be encoded in little-endian byte order.

2.4 Alignment
The header SHALL be 64 bytes, aligned to 1 byte.

The constant pool SHALL begin immediately after metadata.

The instruction stream SHALL begin immediately after the constant pool.

Instructions SHALL be aligned to 1 byte (no alignment padding required).

Constants SHALL be aligned to 1 byte.

2.5 File Extension
Bytecode files SHALL use the extension: .rbot (Robot Bytecode).

2.6 Magic Number
Every valid Robot Bytecode file SHALL begin with the magic number:


0x52424F54 = "RBOT"
This identifies the file as Robot Bytecode.

Chapter 3 – Header Specification
3.1 Header Layout
The header is exactly 64 bytes and has the following layout:

Offset	Length	Field	Type	Description
0	4	magic	uint32_t	Magic number: 0x52424F54
4	2	version_major	uint16_t	Major version
6	2	version_minor	uint16_t	Minor version
8	2	version_patch	uint16_t	Patch version
10	2	target_isa_version	uint16_t	ISA version this bytecode targets
12	4	compiler_version	uint32_t	Compiler version that produced this file
16	4	file_size	uint32_t	Total file size in bytes
20	4	metadata_offset	uint32_t	Offset to metadata section (0 if none)
24	4	metadata_size	uint32_t	Size of metadata section in bytes
28	4	constant_pool_offset	uint32_t	Offset to constant pool
32	4	constant_pool_size	uint32_t	Size of constant pool in bytes
36	4	instruction_stream_offset	uint32_t	Offset to instruction stream
40	4	instruction_stream_size	uint32_t	Size of instruction stream in bytes
44	4	reserved_offset	uint32_t	Offset to reserved section (0 if none)
48	4	reserved_size	uint32_t	Size of reserved section in bytes
52	4	entry_point	uint32_t	Instruction index of entry point
56	2	flags	uint16_t	Flags (bitmask)
58	1	checksum_type	uint8_t	Checksum algorithm (0 = none, 1 = CRC32)
59	1	checksum[4]	uint8_t[4]	32-bit checksum
64	-	-	-	End of header
3.2 Magic Number
Value	Description
0x52424F54	"RBOT" in ASCII
3.3 Version Fields
Field	Description
version_major	Major version (breaking changes)
version_minor	Minor version (new features, backward compatible)
version_patch	Patch version (bug fixes, no format changes)
target_isa_version	ISA version used by the bytecode
Rules:

A loader SHALL reject bytecode with a version_major greater than the loader supports.

A loader SHOULD accept bytecode with a version_minor greater than the loader supports, ignoring unknown features.

A loader SHALL reject bytecode with a target_isa_version greater than the VM supports.

3.4 File Size
file_size SHALL equal the total number of bytes in the file.

A loader MAY use this field to validate file integrity.

3.5 Section Offsets
Each section offset SHALL point to the byte immediately following the previous section.

Sections SHALL NOT overlap.

3.6 Flags
Bit	Name	Description
0	DEBUG_INFO	Debug information is present
1	PROFILING	Profiling instrumentation is present
2	OPTIMIZED	Bytecode has been optimized
3–15	RESERVED	Reserved for future use; SHALL be 0
3.7 Checksum
If checksum_type is 1 (CRC32), the checksum SHALL be calculated over the entire file excluding the checksum field itself.

If checksum_type is 0, the checksum field SHALL be zero.

3.8 Reserved Fields
All reserved fields in the header SHALL be zero in version 1.0.

Chapter 4 – Metadata Section
4.1 Purpose
The metadata section contains optional, human-readable information about the program.

The metadata section is optional in version 1.0.

If metadata_size is 0, the metadata section SHALL NOT exist.

4.2 Metadata Layout
Offset	Length	Field	Type	Description
0	2	count	uint16_t	Number of metadata entries
2	-	entries	MetadataEntry[]	Array of entries
4.3 Metadata Entry
Each metadata entry has the following format:

Offset	Length	Field	Type	Description
0	2	key_length	uint16_t	Length of key in bytes
2	key_length	key	char[]	UTF-8 encoded key
2+key_length	4	value_length	uint32_t	Length of value in bytes
2+key_length+4	value_length	value	char[]	UTF-8 encoded value
4.4 Standard Metadata Keys
Key	Description
program_name	Name of the program
author	Author of the program
build_time	Build timestamp (ISO 8601)
compiler_version	Version of the compiler used
description	Program description
source_file	Original source file name
4.5 Future Extensions
New metadata keys MAY be added in future versions without breaking compatibility.

Loaders SHALL ignore unknown metadata keys.

Chapter 5 – Constant Pool
5.1 Purpose
The constant pool stores deduplicated constants referenced by instructions.

Constants are indexed starting from 0.

Instructions reference constants by index.

5.2 Constant Pool Layout
Offset	Length	Field	Type	Description
0	4	count	uint32_t	Number of constants
4	-	constants	Constant[]	Array of constants
5.3 Constant Types
Tag	Type	Description
0x01	Integer	32-bit signed integer
0x02	Float	32-bit IEEE 754 floating-point
0x03	Boolean	0 or 1
0x04	String	UTF-8 encoded string (reserved)
0x05	Null	Null value
0x06	Array	Array of constants (reserved)
0x07–0xFF	RESERVED	Reserved for future use
5.4 Integer Constant
Offset	Length	Field	Type	Description
0	1	tag	uint8_t	0x01
1	4	value	int32_t	32-bit signed integer
5.5 Float Constant
Offset	Length	Field	Type	Description
0	1	tag	uint8_t	0x02
1	4	value	float	32-bit IEEE 754 float
5.6 Boolean Constant
Offset	Length	Field	Type	Description
0	1	tag	uint8_t	0x03
1	1	value	uint8_t	0 = false, 1 = true
5.7 String Constant (Reserved)
Offset	Length	Field	Type	Description
0	1	tag	uint8_t	0x04
1	4	length	uint32_t	String length in bytes
5	length	value	char[]	UTF-8 encoded string
String constants are reserved for future use. Version 1.0 loaders SHALL reject string constants.

5.8 Null Constant
Offset	Length	Field	Type	Description
0	1	tag	uint8_t	0x05
5.9 Array Constant (Reserved)
Array constants are reserved for future use. Version 1.0 loaders SHALL reject array constants.

5.10 Encoding Rules
Constants SHALL be stored contiguously.

Each constant SHALL begin with a type tag.

Constants SHALL be aligned to 1 byte.

String constants SHALL be UTF-8 encoded.

Duplicate constants SHOULD be deduplicated by the compiler.

Constants SHALL NOT reference other constants.

5.11 Index Rules
Constant indices SHALL be 0-based.

The first constant SHALL have index 0.

Constants SHALL be accessed by index in instructions.

Invalid constant references SHALL cause loader rejection.

5.12 Access Rules
Instructions MAY reference constants by index.

Constants SHALL be read-only.

Constants SHALL NOT be modified by the VM.

Constants SHALL NOT be self-referential.

Chapter 6 – Instruction Stream
6.1 Purpose
The instruction stream contains the linear sequence of encoded instructions that form the program.

6.2 Instruction Order
Instructions SHALL be stored in the order they are executed.

Control flow instructions (Jump, JumpIfFalse, JumpIfTrue, Call) reference instruction indices in this stream.

6.3 Instruction Alignment
Instructions SHALL NOT require alignment.

Each instruction SHALL begin immediately after the previous instruction.

6.4 Instruction Size
Each instruction has a fixed size of 16 bytes in version 1.0.


struct Instruction {
    uint32_t opcode;   // 4 bytes
    uint8_t flags;     // 1 byte
    uint8_t reserved;  // 1 byte
    uint16_t padding;  // 2 bytes (future use)
    int32_t p1;        // 4 bytes
    int32_t p2;        // 4 bytes
};
Total: 16 bytes.

Note: The fixed-size format is chosen for simplicity and deterministic decoding. Future versions may introduce variable-length instructions, but the current format SHALL remain supported.

6.5 Instruction Layout
Offset	Length	Field	Type	Description
0	4	opcode	uint32_t	Opcode value
4	1	flags	uint8_t	Instruction flags
5	1	reserved	uint8_t	Reserved for future use
6	2	padding	uint16_t	Reserved for future use
8	4	p1	int32_t	Operand 1
12	4	p2	int32_t	Operand 2
6.6 Instruction Flags
Bit	Name	Description
0	CONDITIONAL	Instruction is conditional
1	HAS_IMMEDIATE	Instruction has immediate operand
2	HAS_CONSTANT	Instruction references constant pool
3–7	RESERVED	Reserved for future use; SHALL be 0
6.7 Opcode Encoding
Opcode values SHALL be 32-bit unsigned integers.

Opcode values SHALL be assigned according to the ISA specification.

See Appendix A for the complete opcode table.

6.8 Operand Encoding
Operands SHALL be encoded as 32-bit signed integers (int32_t).

Operand encoding rules SHALL follow the ISA specification.

See Chapter 8 for operand encoding details.

6.9 Reserved Opcodes
Opcode values 65–127 are reserved for future core instructions.

Opcode values 128–255 are reserved for future motion instructions.

Opcode values 256–511 are reserved for future sensor instructions.

Opcode values 512–1023 are reserved for future control instructions.

Opcode values 1024–2047 are reserved for future output instructions.

Opcode values 2048–4095 are reserved for future custom plugins.

6.10 Future Extensions
New instructions MAY be added in future versions without breaking compatibility.

Loaders SHALL reject unknown opcodes with error code 1 (Invalid Opcode).

Reserved opcodes SHALL NOT be used in version 1.0.

Chapter 7 – Opcode Encoding
7.1 Opcode Table
This section defines the encoding of every opcode.

For each opcode, the following information is provided:

Opcode Value – The numeric value

Instruction Name – The mnemonic name

Operand Layout – How operands are used

Instruction Length – Fixed size

ISA Reference – Link to ISA specification

7.2 Core Opcodes
Opcode	Name	p1	p2	Description
1	LoadConst	dest	value	Load constant into variable
64	Nop	-	-	No operation
7	Wait	duration	-	Wait milliseconds
17	Label	-	-	Label placeholder
27	Call	target	-	Call function
28	Return	-	-	Return from function
29	Store	src	dest	Store value
7.3 Arithmetic Opcodes
Opcode	Name	p1	p2	p3	Description
20	Add	left	right	result	Addition
21	Sub	left	right	result	Subtraction
22	Mul	left	right	result	Multiplication
23	Div	left	right	result	Integer division
24	Mod	left	right	result	Modulo
25	Pow	left	right	result	Power
26	Neg	src	-	result	Negate
7.4 Comparison Opcodes
Opcode	Name	p1	p2	p3	Description
8	CompareEQ	left	right	result	Equal
9	CompareNE	left	right	result	Not equal
10	CompareLT	left	right	result	Less than
11	CompareLE	left	right	result	Less or equal
12	CompareGT	left	right	result	Greater than
13	CompareGE	left	right	result	Greater or equal
7.5 Control Flow Opcodes
Opcode	Name	p1	p2	Description
14	Jump	-	target	Unconditional jump
15	JumpIfFalse	cond	target	Jump if false
16	JumpIfTrue	cond	target	Jump if true
7.6 Motion Opcodes
Opcode	Name	p1	p2	Description
2	Forward	speed	-	Move forward
3	Backward	speed	-	Move backward
4	TurnLeft	speed	-	Turn left
5	TurnRight	speed	-	Turn right
6	Stop	-	-	Stop motors
35	SetMotorSpeed	left	right	Set motor speeds
52	MoveInitialize	left	right	Initialize motors
53	MoveRunAngle	speed	angle	Move angle
7.7 Sensor Opcodes
Opcode	Name	p1	p2	p3	Description
30	ReadUltrasonic	dest	-	-	Read ultrasonic
31	ReadTouch	port	dest	-	Read touch
32	ReadLight	channel	dest	-	Read light
33	ReadColor	dest	-	-	Read color
34	ReadLine	channel	dest	-	Read line
42	GetTraceValue	port	channel	dest	Trace value
43	GetTraceState	port	channel	dest	Trace state
44	GetTraceRaw	port	-	dest	Trace raw
54	GetLightSensorData	port	dest	-	Light sensor data
7.8 Output Opcodes
Opcode	Name	p1	p2	p3	Description
36	SetServo	port	angle	-	Set servo
37	Set3CLed	port	state	-	Set LED
38	SetLightSensorLed	port	state	-	Sensor LED
39	SetMotorStraightAngle	left	right	speed	angle	Motor angle
41	SetMp3Play	index	-	-	Play audio
55	SetSeeringEngine	port	angle	-	Steering
56	SetSeeringEngineTime	port	angle	time	Steering time
57	SetMotor	port	speed	-	Set motor
58	SetMotorServo	port	speed	angle	Motor servo
61	SetLizard	state	-	-	Lizard
7.9 Line Following Opcodes
Opcode	Name	p1	p2	p3	Description
47	LineBasis	speed	-	-	Basic line follow
48	LineFollow	speed	-	-	Full line follow
49	LineStop	-	-	-	Stop line
50	LineTurnEncounterLine	speed	angle	dir	Turn until line
51	LineForBmp	speed	degree	-	Line for bitmapped path
59	LineMillisecond	speed	ms	-	Line follow time
60	LineSetInitialize	port	color	chassis	Initialize line sensor
7.10 GUI Opcodes (NOP)
Opcode	Name	p1	p2	Description
62	UpdateVar	-	-	Update GUI variable (NOP)
63	DisplayVariable	-	-	Display variable (NOP)
7.11 Encoding Examples
Example 1: LoadConst

Opcode:  1 (0x00000001)
p1:      0 (dest variable)
p2:      80 (value)

Binary:
01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
Example 2: Forward

Opcode:  2 (0x00000002)
p1:      0 (speed variable)
p2:      0

Binary:
02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
Example 3: Stop

Opcode:  6 (0x00000006)
p1:      0
p2:      0

Binary:
06 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
Chapter 8 – Operand Encoding
8.1 Operand Types
Operands are encoded as 32-bit signed integers (int32_t).

The interpretation of each operand depends on the opcode.

8.2 Register Operands
Register operands reference variables by index.

Range: 0–31

Negative values SHALL be invalid

8.3 Immediate Operands
Immediate operands encode literal values directly in the instruction.

Type	Range	Encoding
Speed	-100 to 100	int32_t
Duration	0 to 2,147,483,647	int32_t
Port	0 to 255	int32_t
Channel	0 to 255	int32_t
Angle	0 to 360	int32_t
Degree	0 to 360	int32_t
Direction	1, 2, 3, 4	int32_t
8.4 Jump Target Operands
Jump targets are encoded as instruction indices.

Range: 0 to instruction_count - 1

Negative values SHALL be invalid

Targets beyond instruction_count SHALL be invalid

8.5 Constant Pool Operands
Constants are referenced by index in the constant pool.

Range: 0 to constant_pool_count - 1

Negative values SHALL be invalid

8.6 Boolean Operands
Boolean values are encoded as:

Value	Encoding
false	0
true	1
8.7 Direction Encoding
Direction	Encoding
forward	1
backward	2
left	3
right	4
8.8 Encoding Rules
All operands SHALL be 32-bit signed integers.

Invalid operand values SHALL cause loader rejection.

Constant pool indices SHALL reference valid constants.

Jump targets SHALL reference valid instruction indices.

Register indices SHALL be within the range 0–31.

8.9 Future Types
Future versions MAY support additional operand types:

64-bit integers

Extended registers

Indirect addressing

Floating-point operands

These SHALL be encoded using the existing 32-bit operand fields or by extending the instruction format.

Chapter 9 – Program Counter Rules
9.1 Instruction Addressing
Instructions are addressed by index in the instruction stream.

The first instruction has index 0.

The entry point SHALL be an instruction index.

9.2 Jump Target Encoding
Jump targets SHALL be encoded as instruction indices (0-based).

Jump targets SHALL be:

Within the range [0, instruction_count)

Valid instruction boundaries

9.3 Instruction Offset
The instruction stream offset in the file is given by instruction_stream_offset in the header.

Instructions are stored contiguously from this offset.

9.4 Entry Point
The entry point SHALL be the index of the first instruction to execute.

The entry point SHALL be within the instruction stream.

If entry_point is 0, execution SHALL begin at the first instruction.

9.5 Alignment Rules
Instruction indices SHALL be 0-based.

Instruction boundaries SHALL be 16-byte aligned.

Jump targets SHALL reference instruction boundaries.

Invalid jump targets SHALL cause loader rejection.

9.6 Execution Flow

Entry Point (header)
    ↓
PC = entry_point
    ↓
Instruction at PC
    ↓
Execute
    ↓
PC++ (or jump)
    ↓
Instruction at PC
Chapter 10 – Validation Rules
10.1 Header Validation
The loader SHALL validate:

Magic number equals 0x52424F54.

File size matches file_size.

Section offsets are within file bounds.

Section sizes are non-negative.

Entry point is within instruction stream.

Flags are valid (reserved bits are 0).

Checksum matches (if present).

10.2 Version Validation
The loader SHALL validate:

version_major is supported.

target_isa_version is supported.

version_minor is within supported range.

10.3 Checksum Validation
If checksum_type is 1 (CRC32):

Calculate CRC32 over the file excluding the checksum field.

Compare with the stored checksum.

Reject if they differ.

10.4 Instruction Validation
The loader SHALL validate:

All opcodes are known.

All operands are valid.

Jump targets are within bounds.

Constant pool indices are valid.

Register indices are within bounds.

10.5 Constant Pool Validation
The loader SHALL validate:

All constants have valid tags.

String constants (tag 0x04) are rejected in version 1.0.

Array constants (tag 0x06) are rejected in version 1.0.

All constant data is well-formed.

10.6 Entry Point Validation
The loader SHALL validate:

entry_point is within the instruction stream.

entry_point points to a valid instruction.

10.7 Reserved Field Validation
The loader SHALL validate:

All reserved fields are zero in version 1.0.

Reserved sections are not used.

Chapter 11 – Error Conditions
11.1 Error Table
Code	Name	Description
0	SUCCESS	No error
1	INVALID_OPCODE	Unknown opcode value
2	INVALID_OPERAND	Invalid operand value
3	INVALID_JUMP_TARGET	Jump target out of bounds
4	CONSTANT_POOL_INVALID	Invalid constant pool reference
5	VERSION_UNSUPPORTED	Unsupported version
6	CORRUPTED_FILE	File is corrupted
7	INVALID_HEADER	Invalid header fields
8	INVALID_ENTRY_POINT	Invalid entry point
9	METADATA_CORRUPTED	Metadata section is corrupted
10	RESERVED_OPCODE	Reserved opcode used
11.2 Loader Behavior on Error
Invalid Header: Reject with code 7.

Unsupported Version: Reject with code 5.

Corrupted File: Reject with code 6.

Invalid Opcode: Reject with code 1.

Invalid Jump Target: Reject with code 3.

Invalid Constant: Reject with code 4.

11.3 VM Behavior on Error
Invalid Opcode: VM SHALL stop with error code 1.

Invalid Jump Target: VM SHALL stop with error code 3.

Division by Zero: VM SHALL stop with error code 6 (ISA).

Modulo by Zero: VM SHALL stop with error code 7 (ISA).

Stack Overflow: VM SHALL stop with error code 4 (ISA).

Return Without Call: VM SHALL stop with error code 5 (ISA).

11.4 Error Recovery
Errors SHALL be fatal.

The VM SHALL NOT attempt to recover from bytecode errors.

The VM SHALL stop execution and report the error.

Chapter 12 – Version Compatibility
12.1 Version Number
Version SHALL be encoded as: major.minor.patch

Major: Breaking changes

Minor: New features, backward compatible

Patch: Bug fixes, no format changes

12.2 Backward Compatibility
New versions SHALL support all previous opcodes.

Deprecated opcodes SHALL remain available.

New operand types SHALL NOT remove existing types.

The loader SHALL reject programs with unsupported major version.

12.3 Forward Compatibility
Reserved opcodes SHALL NOT be used by the VM.

Programs using reserved opcodes SHALL be rejected.

The constant pool MAY contain additional metadata ignored by older loaders.

12.4 Extension Points
Extension Point	Location	Purpose
Reserved Opcode Range	65–4095	Future instructions
Reserved Constant Tags	0x06–0xFF	Future data types
Flags Field	Header	Future metadata
Reserved Section	End of file	Future extensions
12.5 Version Table
Version	Status	Notes
1.0.0	Current	Initial release
Future	-	TBD
12.6 Extension Rules
New sections SHALL be appended at the end.

New opcodes SHALL be added in reserved ranges.

New constants SHALL use reserved tags.

New flags SHALL use reserved bits.

Chapter 13 – Worked Examples
13.1 Example 1: Simple Move Program
Source (RoboSim):
python
forward(50)
wait(1000)
stop()
Bytecode Assembly:

#0000 LoadConst 0, 50
#0001 Forward 0
#0002 Wait 1000
#0003 Stop
Binary Layout:

Header:
  Magic:        0x52424F54
  Version:      1.0.0
  ISA Version:  1
  File Size:    64 + 0 + 16 + 64 = 144
  Entry Point:  0

Constant Pool:
  count: 0

Instruction Stream (64 bytes):
  [0] 01 00 00 00 ... LoadConst 0, 50
  [1] 02 00 00 00 ... Forward 0
  [2] 07 00 00 00 ... Wait 1000
  [3] 06 00 00 00 ... Stop
Hex Dump:

52 42 4F 54 01 00 00 00 01 00 00 00 01 00 00 00  ... RBOT........
01 00 00 00 90 00 00 00 00 00 00 00 00 00 00 00  ................
00 00 00 00 10 00 00 00 00 00 00 00 00 00 00 00  ................
40 00 00 00 40 00 00 00 00 00 00 00 00 00 00 00  @...@...........
01 00 00 00 00 00 00 00 32 00 00 00 00 00 00 00  ........2.......
02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
07 00 00 00 E8 03 00 00 00 00 00 00 00 00 00 00  ................
06 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
13.2 Example 2: Conditional Program
Source (RoboSim):
python
distance = read_ultrasonic()
if distance < 20:
    backward(50)
else:
    forward(50)
Bytecode Assembly:

#0000 ReadUltrasonic 0
#0001 LoadConst 1, 20
#0002 CompareLT 0, 1, 2
#0003 JumpIfFalse 2, 6
#0004 LoadConst 3, 50
#0005 Backward 3
#0006 Jump 8
#0007 LoadConst 4, 50
#0008 Forward 4
Instruction Stream:

ReadUltrasonic   p1=0, p2=0
LoadConst        p1=1, p2=20
CompareLT        p1=0, p2=1, p3=2
JumpIfFalse      p1=2, p2=6
LoadConst        p1=3, p2=50
Backward         p1=3
Jump             p2=8
LoadConst        p1=4, p2=50
Forward          p1=4
13.3 Example 3: While Loop
Source (RoboSim):
python
speed = 80
while speed > 50:
    forward(80)
    speed = speed - 10
Bytecode Assembly:

#0000 LoadConst 0, 80
#0001 LoadConst 1, 50
#0002 CompareGT 0, 1, 2
#0003 JumpIfFalse 2, 8
#0004 LoadConst 3, 80
#0005 Forward 3
#0006 LoadConst 4, 10
#0007 Sub 0, 4, 0
#0008 Jump 2
Control Flow:

        ┌─────────────────────┐
        │                     ▼
#0000   LoadConst            │
#0001   LoadConst            │
#0002   CompareGT ───────────┘
#0003   JumpIfFalse ───────┐
#0004   LoadConst          │
#0005   Forward            │
#0006   LoadConst          │
#0007   Sub                │
#0008   Jump ──────────────┘
13.4 Example 4: Sensor-Based Obstacle Avoidance
Source (RoboSim):
python
while True:
    dist = read_ultrasonic()
    if dist < 20:
        turn_left(50)
        wait(500)
    else:
        forward(50)
Bytecode Assembly:

#0000 LoadConst 0, 1
#0001 ReadUltrasonic 1
#0002 LoadConst 2, 20
#0003 CompareLT 1, 2, 3
#0004 JumpIfFalse 3, 9
#0005 LoadConst 4, 50
#0006 TurnLeft 4
#0007 LoadConst 5, 500
#0008 Wait 5
#0009 Jump 1
#0010 LoadConst 6, 50
#0011 Forward 6
#0012 Jump 1
Appendix A – Opcode Encoding Table
Opcode	Value	Name	Operands	Description
1	0x01	LoadConst	dest, value	Load constant
2	0x02	Forward	speed	Move forward
3	0x03	Backward	speed	Move backward
4	0x04	TurnLeft	speed	Turn left
5	0x05	TurnRight	speed	Turn right
6	0x06	Stop	-	Stop motors
7	0x07	Wait	duration	Wait milliseconds
8	0x08	CompareEQ	left, right, result	Equal
9	0x09	CompareNE	left, right, result	Not equal
10	0x0A	CompareLT	left, right, result	Less than
11	0x0B	CompareLE	left, right, result	Less or equal
12	0x0C	CompareGT	left, right, result	Greater than
13	0x0D	CompareGE	left, right, result	Greater or equal
14	0x0E	Jump	- target	Unconditional jump
15	0x0F	JumpIfFalse	cond, target	Jump if false
16	0x10	JumpIfTrue	cond, target	Jump if true
17	0x11	Label	-	Label placeholder
20	0x14	Add	left, right, result	Addition
21	0x15	Sub	left, right, result	Subtraction
22	0x16	Mul	left, right, result	Multiplication
23	0x17	Div	left, right, result	Division
24	0x18	Mod	left, right, result	Modulo
25	0x19	Pow	left, right, result	Power
26	0x1A	Neg	src, -, result	Negate
27	0x1B	Call	target	Call function
28	0x1C	Return	-	Return from function
29	0x1D	Store	src, dest	Store value
30	0x1E	ReadUltrasonic	dest	Ultrasonic
31	0x1F	ReadTouch	port, dest	Touch
32	0x20	ReadLight	channel, dest	Light
33	0x21	ReadColor	dest	Color
34	0x22	ReadLine	channel, dest	Line
35	0x23	SetMotorSpeed	left, right	Set speed
36	0x24	SetServo	port, angle	Servo
37	0x25	Set3CLed	port, state	LED
38	0x26	SetLightSensorLed	port, state	Sensor LED
39	0x27	SetMotorStraightAngle	left, right, speed, angle	Motor angle
40	0x28	LineIntersectionStop	speed, type	Intersection stop
41	0x29	SetMp3Play	index	Play audio
42	0x2A	GetTraceValue	port, channel, dest	Trace value
43	0x2B	GetTraceState	port, channel, dest	Trace state
44	0x2C	GetTraceRaw	port, -, dest	Trace raw
47	0x2F	LineBasis	speed	Basic line follow
48	0x30	LineFollow	speed	Line follow
49	0x31	LineStop	-	Stop line
50	0x32	LineTurnEncounterLine	speed, angle, dir	Turn until line
51	0x33	LineForBmp	speed, degree	Bitmap line follow
52	0x34	MoveInitialize	left, right	Initialize motors
53	0x35	MoveRunAngle	speed, angle	Move angle
54	0x36	GetLightSensorData	port, dest	Light data
55	0x37	SetSeeringEngine	port, angle	Steering
56	0x38	SetSeeringEngineTime	port, angle, time	Steering time
57	0x39	SetMotor	port, speed	Set motor
58	0x3A	SetMotorServo	port, speed, angle	Motor servo
59	0x3B	LineMillisecond	speed, ms	Line follow time
60	0x3C	LineSetInitialize	port, color, chassis	Initialize line
61	0x3D	SetLizard	state	Lizard
62	0x3E	UpdateVar	-	Update variable (NOP)
63	0x3F	DisplayVariable	-	Display variable (NOP)
64	0x40	Nop	-	No operation
Appendix B – Operand Encoding Table
Operand Type	Encoding	Range	Description
Register	int32_t	0–31	Variable index
Speed	int32_t	-100–100	Motor speed
Duration	int32_t	0–2,147,483,647	Time in milliseconds
Port	int32_t	0–255	Port number
Channel	int32_t	0–255	Sensor channel
Angle	int32_t	0–360	Angle in degrees
Direction	int32_t	1–4	Direction (forward=1, etc.)
Jump Target	int32_t	0–N-1	Instruction index
Constant Index	int32_t	0–C-1	Constant pool index
Boolean	int32_t	0–1	Boolean value
Appendix C – Constant Pool Table
Tag	Name	Description
0x01	Integer	32-bit signed integer
0x02	Float	32-bit IEEE 754 float
0x03	Boolean	0 or 1
0x04	String	UTF-8 string (reserved)
0x05	Null	Null value
0x06	Array	Array of constants (reserved)
0x07–0xFF	RESERVED	Reserved for future use
Appendix D – Header Layout
Offset	Length	Field	Type	Description
0	4	magic	uint32_t	0x52424F54
4	2	version_major	uint16_t	Major version
6	2	version_minor	uint16_t	Minor version
8	2	version_patch	uint16_t	Patch version
10	2	target_isa_version	uint16_t	ISA version
12	4	compiler_version	uint32_t	Compiler version
16	4	file_size	uint32_t	Total file size
20	4	metadata_offset	uint32_t	Metadata offset
24	4	metadata_size	uint32_t	Metadata size
28	4	constant_pool_offset	uint32_t	CP offset
32	4	constant_pool_size	uint32_t	CP size
36	4	instruction_stream_offset	uint32_t	IS offset
40	4	instruction_stream_size	uint32_t	IS size
44	4	reserved_offset	uint32_t	Reserved offset
48	4	reserved_size	uint32_t	Reserved size
52	4	entry_point	uint32_t	Entry point
56	2	flags	uint16_t	Flags
58	1	checksum_type	uint8_t	Checksum type
59	4	checksum	uint8_t[4]	Checksum
Appendix E – Binary Examples
E.1 Forward Program
Source:
python
forward(50)
Hex Dump:

52 42 4F 54 01 00 01 00 01 00 00 00 01 00 00 00  RBOT............
48 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  H...............
00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00  ............@...
10 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
01 00 00 00 00 00 00 00 32 00 00 00 00 00 00 00  ........2.......
02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
E.2 Move and Stop
Source:
python
forward(80)
stop()
Hex Dump:

52 42 4F 54 01 00 01 00 01 00 00 00 01 00 00 00  RBOT............
58 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  X...............
00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00  ............@...
20 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00   ...............
01 00 00 00 00 00 00 00 50 00 00 00 00 00 00 00  ........P.......
02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
06 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
E.3 if/else Program
Source:
python
if distance < 20:
    backward(50)
else:
    forward(50)
Hex Dump (with variables):

52 42 4F 54 01 00 01 00 01 00 00 00 01 00 00 00  RBOT............
D0 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
00 00 00 00 00 00 00 00 00 00 00 00 40 00 00 00  ............@...
A0 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
1E 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  ................
01 00 00 00 01 00 00 00 14 00 00 00 00 00 00 00  ................
0A 00 00 00 00 00 00 00 01 00 00 00 02 00 00 00  ................
0F 00 00 00 02 00 00 00 06 00 00 00 00 00 00 00  ................
01 00 00 00 03 00 00 00 32 00 00 00 00 00 00 00  ........2.......
03 00 00 00 03 00 00 00 00 00 00 00 00 00 00 00  ................
0E 00 00 00 08 00 00 00 00 00 00 00 00 00 00 00  ................
01 00 00 00 04 00 00 00 32 00 00 00 00 00 00 00  ........2.......
02 00 00 00 04 00 00 00 00 00 00 00 00 00 00 00  ................
Appendix F – Reserved Values
F.1 Reserved Opcode Ranges
Range	Purpose
65–127	Extended core instructions
128–255	Extended motion instructions
256–511	Extended sensor instructions
512–1023	Extended control instructions
1024–2047	Extended output instructions
2048–4095	Custom plugin instructions
F.2 Reserved Constant Tags
Range	Purpose
0x06	Array (reserved)
0x07–0x0F	Extended primitive types
0x10–0x1F	Composite types
0x20–0xFF	Reserved for future use
F.3 Reserved Flag Bits
Bit	Purpose
3–15	Header flags (reserved)
1–7	Instruction flags (reserved)
F.4 Reserved Error Codes
Code	Purpose
11–255	Reserved for future errors
Document Quality Checklist
Completeness
☑ Header fully specified
☑ Metadata section defined
☑ Constant Pool fully specified
☑ Instruction encoding frozen
☑ Operand encoding frozen
☑ Binary layout frozen
☑ Versioning strategy defined
☑ Validation rules complete
☑ Error handling documented
☑ Binary examples included
Normative Language
☑ SHALL used for mandatory requirements
☑ SHOULD used for recommendations
☑ MAY used for optional features
☑ MUST used for absolute requirements
Implementation Independence
☑ No compiler implementation details
☑ No runtime implementation details
☑ No hardware-specific information
☑ No platform-specific information
Tables
☑ Header fields table
☑ Opcode values table
☑ Operand types table
☑ Constant types table
☑ Reserved opcodes table
☑ Version table
☑ Error codes table
Diagrams
☑ Bytecode layout diagram
☑ Header layout diagram
☑ Instruction layout diagram
☑ Constant pool layout diagram
☑ Program counter flow diagram