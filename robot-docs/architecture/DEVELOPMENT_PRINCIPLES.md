# DEVELOPMENT_PRINCIPLES.md

Version: 1.0

Status: Architecture Freeze

Owner: Robot Platform Team

---

# 1. Purpose

This document defines the engineering principles of the Robot Platform.

It answers one question:

> How should developers think when designing the Robot Platform?

Implementation changes over time.

Principles do not.

This document is therefore considered permanent architecture.

---

# 2. Platform Philosophy

The Robot Platform is NOT firmware.

The Robot Platform is NOT an Arduino project.

The Robot Platform is an execution platform for educational robotics.

Everything shall be designed from the perspective of platform engineering.

---

# 3. Primary Goal

The primary goal is

Language Compatibility.

NOT

Hardware Compatibility.

NOT

Feature Count.

NOT

Robot Behaviours.

If a RoboSim program can execute correctly without modification,

the Platform succeeds.

---

# 4. Separation of Responsibility

Every layer owns exactly one responsibility.

Language

↓

defines syntax.

Compiler

↓

generates bytecode.

Runtime

↓

executes bytecode.

RobotAPI

↓

provides robot abstraction.

HAL

↓

controls hardware.

Hardware

↓

performs electrical operations.

Responsibilities shall never overlap.

---

# 5. Single Source of Truth

Every piece of information must exist only once.

Example

API Definition

↓

api.yaml

Everything else

↓

Generated

Never duplicate metadata.

Never synchronize manually.

---

# 6. Generated Artifacts

Generated files are read-only.

Developers SHALL NEVER modify

Generated SDK

Generated Registry

Generated Documentation

Generated Opcode Tables

Changes always begin from the source definition.

---

# 7. Platform Independence

The platform must never depend on

ESP32

STM32

RP2040

Linux

Robot model

Only HAL changes.

Everything above HAL remains unchanged.

---

# 8. Compatibility First

Adding a new feature shall never reduce compatibility.

Compiler compatibility

↓

highest priority.

Runtime compatibility

↓

second.

Hardware compatibility

↓

third.

---

# 9. Behaviour Ownership

Robot behaviours belong to users.

Examples

Line Following

Obstacle Avoidance

Maze

Automatic Parking

Wall Following

Color Sorting

These are educational examples.

They SHALL NOT become Platform code.

The Platform only provides capabilities.

---

# 10. Language Before Implementation

Every new API must follow

Architecture Review

↓

Language Specification

↓

Semantic Classification

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

Hardware

Implementation without specification is forbidden.

---

# 11. Semantic Driven Design

Semantic defines implementation.

Never implementation defines semantic.

Semantic types

Native

Rewrite

NOP

Approximation

Stub

Dummy

Deprecated

Every API belongs to exactly one Semantic.

---

# 12. Hardware Agnostic Design

RobotAPI never exposes

GPIO

PWM

ADC

Pin Numbers

MCU Registers

Developers program robots,

not microcontrollers.

---

# 13. Dependency Direction

Dependencies only flow downward.

Language

↓

Frontend

↓

Compiler

↓

Runtime

↓

RobotAPI

↓

HAL

↓

Hardware

Reverse dependency is forbidden.

---

# 14. Documentation First

Architecture

↓

Specification

↓

Implementation

↓

Testing

↓

Documentation Update

Documentation is part of implementation.

Documentation is never optional.

---

# 15. Test Strategy

Every feature shall be tested independently.

Language Tests

Compiler Tests

Runtime Tests

HAL Tests

Hardware Tests

Physical Tests

No combined tests without unit validation.

---

# 16. Backward Compatibility

Platform updates shall not break

existing RoboSim programs.

Breaking changes require

Architecture Review

Version Increment

Migration Guide

Compatibility Report

---

# 17. Simplicity

Choose the simplest architecture that remains extensible.

Avoid

Special Cases

Temporary Hacks

Hidden Behaviours

Magic Numbers

Implicit Logic

Prefer explicit design.

---

# 18. Extensibility

Adding

New Robot

↓

HAL only.

Adding

New Sensor

↓

Language

RobotAPI

HAL

No Compiler redesign.

No Runtime redesign.

---

# 19. Error Ownership

Every layer owns its own errors.

Compiler

↓

Syntax

Semantic

Runtime

↓

Execution

RobotAPI

↓

Platform

HAL

↓

Hardware

Errors shall never leak implementation details upward.

---

# 20. Long-term Maintainability

Platform decisions shall prioritise

10-year maintainability

over

short-term implementation speed.

Every architectural shortcut becomes future technical debt.

---

# 21. Architecture Review

Every architectural modification must answer

Why?

Why not another solution?

What dependency changes?

What future impact?

Can existing programs continue to work?

Architecture Review precedes implementation.

---

# 22. Code Review Principles

Code reviews shall evaluate

Architecture

Correctness

Maintainability

Readability

Compatibility

Performance

Performance alone never justifies poor architecture.

---

# 23. Future Vision

The Platform shall eventually support

Multiple MCUs

Multiple Robot Models

Simulation

Cloud Compilation

Remote Execution

Plugin System

Visual IDE

Without redesigning the architecture.

---

# 24. Definition of Success

The Robot Platform succeeds when

Students think about robots,

not hardware.

Teachers think about lessons,

not firmware.

Developers think about architecture,

not board-specific implementation.

---

# 25. Engineering Motto

"Build a Platform, not a Project."

Every decision should move the system closer to a reusable robotics platform rather than a single-purpose robot firmware.