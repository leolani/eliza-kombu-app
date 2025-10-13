# REFACTORING PLAN.md

This file provides guidance to Claude Code (claude.ai/code) for the current refactoring task.

## Overview

The goal of the refactoring is to enable multiple EMISSOR scenarios running at the same time in the application.

## Main Change

Currently, the EMISSOR scenario takes a central role in the application: A single scenario is created by a central module
in the application, which is then assumed to be the active scenario. This scenario is then used in all places of the
application as the current scenario. This has the disadvantage that the application can be used only for one interaction
at a time.
However, since all modules process events in sequence, one at a time, they could instead just infer the scenario the
event belongs to from the event itself. This would allow modules easily to handle multiple scenarios in parallel.
Creation of the scenario can be moved to the interaction "frontend", i.e. either the robot or Chat UI.

There is a couple of caveats to keep in mind:
- In a couple of places modules may keep scenario specific state in memory, this must be adjusted to keep the state mapped
  to a specific scenario.
- Connecting both a robot and Chat UI front end needs some scenario management between the two, let's focus on the Chat
  UI for now and ignore the robot backend
- Intentions are more complicated to migrate, leave them out for now
- ASR and VAD modules will be left out of this refactoring stage
- Scenario cleanup (removing old scenario data from memory) is out of scope for this stage

## High level refactoring plan

1. Scenario related events already have a scenario ID in their payload, however, make it explicit and add the scenario ID
   as a distinct property to the EventMetadata, next to the topic, with default None
2. Remove the possibility to obtain the current scenario from the Emissor data service and handle the scenario ID in the
   modules by retrieving it from the event itself and passing it on
3. Make all in memory state in the modules scenario specific by storing it in a dict. In this stage of the refactoring
   don't care about cleaning up the scenario data when a scenario is stopped.
4. Move scenario creation from the context module to the Chat UI module. Assume a 1:1 relationship between chat sessions
   and scenarios.
5. Remove the REST API endpoint for getting the current scenario from EmissorDataService


## Definition of done

This stage of the refactoring is done when the scenario is created by the UI instead of a central module, and there is
no central handling of the scenario anymore, i.e. each event is processed in the context of the specific scenario it
belongs to in the application. For this stage of the refactoring the focus is that on the application is still working
afterwards with a single scenario, only created not in a central place anymore, as the intention mechanism in the
application is still working with only a single scenario.

## Modules in Scope

The following modules need to be refactored:
- **ChatUiService**: Move scenario creation here, handle scenario per chat session
- **ElizaService**: Extract scenario ID from events instead of calling EmissorDataClient
- **KeywordService**: Extract scenario ID from events instead of calling EmissorDataClient
- **ContextService**: Remove scenario creation logic (will be moved to ChatUI)
- **EmissorDataFileStorage**: Support multiple concurrent scenarios with dict-based state
- **EmissorDataService**: Remove current scenario endpoint and related logic
- **EmissorDataClient**: Remove get_current_scenario_id() method

The following modules are **out of scope** for this refactoring:
- ASR Service
- VAD Service
- Backend Service
- BDI Service and intentions-related modules

## Testing Strategy

- Create automated test scripts where feasible to verify functionality after each step
- Use manual testing via the Chat UI for cases not covered by automated tests
- After each step, ensure the application still works with a single scenario before proceeding

## Guidelines

Perform the steps in the refactoring plan in sequence. After each step ensure the application is still working as expected.