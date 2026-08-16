# Robot Platform Book

Version 1.0

Architecture Edition

---

# Preface

The Robot Platform is not simply an ESP32 firmware.

It is not an Arduino library.

It is not a collection of drivers.

The Robot Platform is an execution platform designed to transform educational robot programs into deterministic physical behaviour.

This document describes the complete architecture, philosophy and engineering principles behind the Robot Platform.

Its purpose is not only to explain how the system works, but why it was designed this way.

The intended audience includes

• Platform Architects

• Compiler Developers

• Runtime Developers

• HAL Developers

• Robot Studio Developers

• Future Contributors

This book is considered the highest level documentation of the project.

---

# Part I

## Vision

---

### Chapter 1

Why Robot Platform

A robot is more than hardware.

A robot is also

Language

Compiler

Runtime

Execution Engine

RobotAPI

HAL

Developer Tools

Educational Experience

Traditional educational robots tightly couple these layers.

As the project grows this creates technical debt.

The Robot Platform separates every concern into independent layers.

The objective is simple.

Students should think about robots.

Developers should think about architecture.

Nobody should think about GPIO.

---

### Chapter 2

Design Goals

The platform pursues six primary goals.

1.

Hardware Independence

Changing MCU shall never require compiler redesign.

2.

Language Compatibility

Every RoboSim program should execute without modification.

3.

Deterministic Execution

Identical programs produce identical behaviour.

4.

Educational Simplicity

Robot behaviour belongs to students.

5.

Long-Term Maintainability

Architecture is preferred over shortcuts.

6.

Extensibility

Future hardware requires HAL changes only.

---

# Part II

## Overall Architecture

---

### Chapter 3

System Overview

```
Blockly

↓

Python

↓

Frontend

↓

Compiler

↓

Robot Bytecode

↓

Execution Engine

↓

RobotAPI

↓

HAL

↓

Hardware
```

Every layer owns one responsibility.

Dependencies always point downward.

---

### Chapter 4

Architecture Principles

Single Responsibility

Single Source of Truth

Hardware Independence

Semantic Driven Design

Generated Artifacts

Platform Boundary

Compatibility First

These principles govern every future architectural decision.

---

# Part III

## Language

---

### Chapter 5

Robot Language

The language is defined only once.

```
api.yaml
```

Everything else is generated.

Generated artifacts include

SDK

Compiler Registry

Opcode Tables

Documentation

Compatibility Reports

No generated file shall ever be edited manually.

---

### Chapter 6

Language Evolution

Every new API follows

Architecture Review

↓

Specification

↓

Semantic

↓

Generator

↓

Compiler

↓

Runtime

↓

RobotAPI

↓

HAL

↓

Verification

↓

Documentation

---

# Part IV

## Compiler

---

### Chapter 7

Frontend

The Frontend translates RoboSim specific constructs into Standard Robot API.

Its responsibilities include

Rewrite

Alias Resolution

Legacy Compatibility

Nothing else.

---

### Chapter 8

Compiler

The Compiler transforms Python AST into Robot Bytecode.

Compiler responsibilities

Parsing

Validation

Semantic Checking

Bytecode Generation

Compiler never executes programs.

---

### Chapter 9

Bytecode

Bytecode is platform independent.

It represents robot behaviour in an intermediate executable format.

Execution belongs to the Runtime.

---

# Part V

## Execution Engine

---

### Chapter 10

Execution Philosophy

The Execution Engine is the operating environment of Robot Programs.

It owns

Program Counter

Operand Stack

Call Stack

Variables

Scheduler

Timer

RobotAPI Dispatch

It does not own hardware.

---

### Chapter 11

Execution Cycle

Every instruction executes

Fetch

↓

Decode

↓

Dispatch

↓

Execute

↓

Update Context

↓

Next Instruction

This cycle continues until the program terminates.

---

### Chapter 12

Semantic Execution

Native

↓

RobotAPI

Rewrite

↓

Resolved before execution

NOP

↓

Ignored safely

Stub

↓

Return Not Implemented

Approximation

↓

Equivalent behaviour

Dummy

↓

Deterministic return value

Deprecated

↓

Execute with warning

---

# Part VI

## RobotAPI

---

### Chapter 13

Platform Boundary

RobotAPI is the official boundary between software and hardware.

Everything above RobotAPI is platform.

Everything below RobotAPI is hardware.

RobotAPI never exposes

GPIO

PWM

Registers

Pin Numbers

---

# Part VII

## HAL

---

### Chapter 14

Hardware Abstraction Layer

HAL owns hardware drivers.

Each driver owns one device.

Drivers never execute algorithms.

Drivers never interpret bytecode.

Drivers simply control hardware.

---

# Part VIII

## Compatibility

---

### Chapter 15

Compatibility Philosophy

Compatibility is measured independently.

Language Compatibility

Compiler Compatibility

Runtime Compatibility

Hardware Compatibility

Physical Compatibility

Success requires all five dimensions.

---

### Chapter 16

Semantic Compatibility

Every API belongs to exactly one semantic class.

Native

Rewrite

NOP

Approximation

Stub

Dummy

Deprecated

This guarantees predictable implementation.

---

# Part IX

## Robot Studio

---

### Chapter 17

Developer Experience

Robot Studio is the development environment of the Platform.

Responsibilities include

Code Editing

Compile

Flash

Serial Monitor

Diagnostics

Future Simulation

Robot Studio never performs compilation itself.

It orchestrates the existing toolchain.

---

# Part X

## Engineering

---

### Chapter 18

Development Principles

Architecture before implementation.

Generated artifacts are read-only.

Documentation is part of implementation.

Platform first.

Hardware second.

Every feature requires

Specification

↓

Implementation

↓

Testing

↓

Documentation

---

### Chapter 19

Architecture Decisions

Major architectural decisions are preserved using ADR.

Architecture evolves.

History is never rewritten.

---

# Part XI

## Future

---

### Chapter 20

Platform Roadmap

Language

Compiler

Execution Engine

RobotAPI

HAL

Studio

Cloud

Simulation

Plugin System

The architecture already supports this evolution.

---

# Epilogue

The Robot Platform is not built to control one robot.

It is built to become a reusable execution platform for educational robotics.

Hardware will change.

Programming languages will evolve.

Robot models will improve.

Architecture should remain.

That is the purpose of the Robot Platform.