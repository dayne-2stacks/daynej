# Changelog

## [Unreleased]
- Added initial multi-agent implementations: TriageAgent routes queries to PersonalInfoAgent, ExperienceAgent, and HobbiesAgent with a fallback option.
- Exported new agents from `agents_ext.agents`.
- Added tests for triage routing logic.
- Expanded multi-agent system with BehavioralQuestionAgent, ResumeAgent and CalendarAgent.
- TriageAgent now dynamically routes to all specialized agents.
- Added tests for new routing paths.
- Refactored agents so each specialized agent resides in its own module under
  `agents_ext/agents` and updated `TriageAgent` accordingly.
