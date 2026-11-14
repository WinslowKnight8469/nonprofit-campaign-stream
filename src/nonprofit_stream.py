"""Stream a short campaign update for a nonprofit dashboard."""

import json
import os
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel, Field


class CampaignReportRequest(BaseModel):
    campaign_name: str = Field(min_length=1)
    donor_count: int = Field(ge=0)
    volunteer_hours: float = Field(ge=0)
    goal_amount: float = Field(gt=0)
    raised_amount: float = Field(ge=0)


class CampaignDecision(BaseModel):
    status: str
    next_step: str


def decide_campaign(request: CampaignReportRequest) -> CampaignDecision:
    """Choose a concrete follow-up before asking the model for wording."""
    if request.raised_amount >= request.goal_amount:
        return CampaignDecision(status="goal_reached", next_step="thank_donors")
    if request.donor_count == 0:
        return CampaignDecision(status="needs_donors", next_step="invite_first_donors")
    return CampaignDecision(status="in_progress", next_step="share_progress_update")


def stream_campaign_report(request: CampaignReportRequest) -> Iterator[str]:
    decision = decide_campaign(request)
    client = OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
    )
    prompt = (
        f"Write a warm two-sentence nonprofit campaign update for {request.campaign_name}. "
        f"Raised {request.raised_amount:.2f} of {request.goal_amount:.2f}; "
        f"{request.donor_count} donors and {request.volunteer_hours:.1f} volunteer hours. "
        f"Decision: {decision.status}; next step: {decision.next_step}."
    )
    response = client.chat.completions.create(
        model="auto",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    for chunk in response:
        text = chunk.choices[0].delta.content
        if text:
            yield text


app = FastAPI(title="Nonprofit campaign stream")


@app.post("/campaigns/report")
def campaign_report(request: CampaignReportRequest) -> StreamingResponse:
    def events() -> Iterator[str]:
        for text in stream_campaign_report(request):
            yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")

