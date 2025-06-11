from __future__ import annotations

from ..core.retrieval_agent import RetrievalAgent
from .utils import load_json


def _build_dataset(dayne: dict, extra: list[dict]) -> list[dict]:
    """Combine project and extracurricular experience data."""
    dataset: list[dict] = []
    for proj in dayne.get("Projects", []):
        text = f"{proj.get('Title')}: {proj.get('Description')}"
        dataset.append({"text": text})
    work = dayne.get("WorkAndVolunteeringExperience", {})
    for role in work.get("ProfessionalRoles", []):
        org = (
            role.get("Institution")
            or role.get("Organization")
            or ", ".join(role.get("Organizations", []))
        )
        text = f"{role.get('Title')} at {org}: {role.get('Description')}"
        dataset.append({"text": text})
    for vol in work.get("Volunteering", []):
        dataset.append({"text": vol})
    for lead in dayne.get("Leadership", []):
        org = lead.get("Organization")
        years = lead.get("Years")
        text = f"{lead.get('Role')} with {org} ({years})"
        dataset.append({"text": text})
    dataset.extend(extra)
    return dataset


class ExperienceAgent(RetrievalAgent):
    """Answer questions about Dayne's professional and project experience."""

    def __init__(
        self,
        model: str = "gpt-4o",
        embed_model: str = "text-embedding-3-small",
        rerank_models: list[str] | None = None,
    ) -> None:
        dayne = load_json("dayne.json")
        extra = load_json("experiences.json")
        dataset = _build_dataset(dayne, extra)
        super().__init__(
            "experience",
            data=dataset,
            model=model,
            embed_model=embed_model,
            rerank_models=rerank_models,
        )

    def _get_entry_text(self, entry: dict) -> str:  # type: ignore[override]
        return entry.get("text") or entry.get("answer") or entry.get("question", "")

    def _build_messages(self, question: str) -> list[dict]:
        history = self.memory.messages[-5:]
        context = "\n".join(
            self._get_entry_text(e) for e in self.retrieve(question, k=3)
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "Answer the user's question about Dayne's work experience,"
                    " projects, or extracurricular activities using the"
                    " following information."
                ),
            },
            {"role": "system", "content": f"Relevant info:\n{context}"},
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": question})
        return messages

    async def run(self, message: str) -> str:
        self.add_message("user", message)
        messages = self._build_messages(message)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        content = response.choices[0].message.content.strip()
        self.add_message("assistant", content)
        return content
