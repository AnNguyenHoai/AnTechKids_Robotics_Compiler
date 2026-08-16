# ARCHITECTURE_DECISION_RECORDS.md

Version: 1.0

Status: Living Document

Owner: Robot Platform Team

---

# Purpose

This document records every major architectural decision made during the development of the Robot Platform.

Unlike implementation documents,

ADR explains

WHY

rather than

HOW.

Every architectural change shall create a new ADR.

Existing ADRs shall never be modified.

History must be preserved.

---

# ADR-001

## Title

Robot Platform instead of Robot Firmware

---

### Status

Accepted

---

### Date

2026

---

### Context

The initial implementation evolved from an ESP32 firmware.

As more features were added,

the project gradually became

Language

Compiler

Runtime

RobotAPI

HAL

Robot Studio

instead of only firmware.

Continuing to treat the system as firmware would eventually create tight coupling.

---

### Decision

The project is officially defined as

Robot Platform.

Firmware becomes only one deployment target.

---

### Consequences

Architecture becomes hardware independent.

Future MCUs are supported.

Robot Studio becomes a first-class component.

Educational behaviours remain outside the Platform.

---

# ADR-002

## Title

Bytecode Virtual Machine

---

### Context

Several alternatives were considered.

Python Interpreter

C++ Transpiler

Native Code Generation

Bytecode VM

---

### Decision

Robot programs shall execute through Bytecode.

---

### Rationale

Portable.

Compact.

Deterministic.

Independent from hardware.

Supports multiple platforms.

---

### Consequences

Compiler generates bytecode.

Runtime executes bytecode.

HAL becomes reusable.

---

# ADR-003

## Title

Single Source of Truth

---

### Context

Multiple API definitions existed.

SDK

Registry

Documentation

Compiler

were manually synchronized.

This created inconsistency.

---

### Decision

Language Specification becomes the only source.

Everything else is generated.

Preferred source

api.yaml

---

### Consequences

No duplicated metadata.

No manual synchronization.

Consistent SDK.

Consistent Compiler.

Consistent Documentation.

---

# ADR-004

## Title

Semantic-driven Architecture

---

### Context

Compiler behaviour was becoming increasingly implementation specific.

---

### Decision

Every API must belong to exactly one Semantic.

Native

Rewrite

NOP

Approximation

Stub

Dummy

Deprecated

---

### Consequences

Runtime becomes predictable.

Compatibility becomes measurable.

Implementation strategy becomes standardized.

---

# ADR-005

## Title

Platform does not implement Behaviours

---

### Context

There was discussion about implementing

Line Following

Obstacle Avoidance

Maze

inside Platform.

---

### Decision

Platform only provides capabilities.

Behaviours belong to users.

---

### Consequences

Platform remains generic.

Educational value increases.

Language stays reusable.

---

# ADR-006

## Title

RobotAPI as Platform Boundary

---

### Context

Direct hardware access simplifies implementation but tightly couples Runtime to hardware.

---

### Decision

RobotAPI becomes the only platform abstraction.

Runtime never accesses HAL directly.

---

### Consequences

Changing hardware affects only HAL.

Runtime remains portable.

---

# ADR-007

## Title

HAL owns Hardware

---

### Context

Early implementations allowed Runtime and VM to call drivers directly.

---

### Decision

Only HAL may access hardware.

---

### Consequences

Hardware independence.

Driver isolation.

Cleaner testing.

---

# ADR-008

## Title

Layered Dependency

---

### Decision

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

### Consequences

Clear ownership.

Low coupling.

High maintainability.

---

# ADR-009

## Title

Generated Artifacts are Read-only

---

### Decision

Generated files shall never be edited manually.

All modifications begin from Language Specification.

---

### Consequences

Repeatable builds.

No inconsistent generated code.

---

# ADR-010

## Title

Architecture Before Implementation

---

### Decision

Architecture Freeze precedes implementation.

Every subsystem requires

Architecture

↓

Specification

↓

Implementation

↓

Testing

---

### Consequences

Reduced redesign.

Stable development.

Predictable roadmap.

---

# ADR-011

## Title

Compatibility First

---

### Decision

Compiler Compatibility has higher priority than Runtime optimization.

---

### Rationale

A program that cannot compile has no execution path.

---

### Consequences

Compiler reaches 100% compatibility before Runtime expansion.

---

# ADR-012

## Title

Long-term Maintainability

---

### Decision

Architectural quality has higher priority than implementation speed.

---

### Rationale

The Platform is expected to evolve over many years.

Temporary shortcuts become permanent technical debt.

---

### Consequences

Architecture reviews are mandatory.

Large refactors become unnecessary.

---

# Future ADR

Every future architectural decision shall follow the template.

-----------------------------------

ADR-XXX

Title

Status

Date

Context

Decision

Alternatives

Rationale

Consequences

References

-----------------------------------

Existing ADRs are immutable.

New ideas create new ADRs.

History shall never be rewritten.

---

# Architecture Philosophy

Architecture is a sequence of decisions.

Code changes.

Documentation changes.

Hardware changes.

Architecture decisions remain.

ADR preserves the reasoning behind every important choice made throughout the lifetime of the Robot Platform.