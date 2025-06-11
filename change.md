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
- BehavioralQuestionAgent now uses chat history and OpenAI retrieval to answer
  interview questions based on experiences.json. Added unit tests.
- Introduced ``RetrievalAgent`` base class providing embedding search with a
  second-stage reranker. BehavioralQuestionAgent now inherits from it.
- ``RetrievalAgent`` now defaults to ColBERT-v2 and BGE-M3 checkpoints for
  reranking when ``sentence-transformers`` is available.
