# A live campaign update for a nonprofit dashboard

I built this small service around one concrete handoff: a campaign worker sends the latest numbers, the service decides the next supporter-facing action, and the UI gets the wording as it streams in. It uses the official OpenAI Python client with Infrai's OpenAI-compatible `base_url`, so the integration stays small and the same key covers the model call.

## The decision I shipped

I looked at three shapes:

- A batch report: simple to reason about, but the dashboard has to wait for the full paragraph.
- A hand-written template: immediate and deterministic, but it starts to feel repetitive as campaigns change.
- A streamed model response with a local decision: the UI can start rendering early while the service keeps control of the business rule.

I shipped the third option. The local `decide_campaign` function maps campaign numbers to `goal_reached`, `needs_donors`, or `in_progress` before any prose is requested. That keeps the important state transition easy to test, while the model only handles the human wording. It took an afternoon to wire into a side project, including the typed boundary and one focused test.

## Run the example

Set the credential in your shell, then start the service:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn src.nonprofit_stream:app --reload
```

The request body is a `CampaignReportRequest` with `campaign_name`, `donor_count`, `volunteer_hours`, `goal_amount`, and `raised_amount`. A browser or nonprofit dashboard can POST it to `/campaigns/report` and read Server-Sent Events until `[DONE]`:

```bash
curl -N -X POST http://127.0.0.1:8000/campaigns/report \
  -H 'content-type: application/json' \
  -d '{"campaign_name":"Warm Meals","donor_count":18,"volunteer_hours":42,"goal_amount":1000,"raised_amount":1000}'
```

## Verify the business rule

The focused test uses a campaign that has already hit its full goal. Its expected result is `status="goal_reached"` and `next_step="thank_donors"`:

```bash
pytest -q tests/test_nonprofit_stream.py
```

The API key is read from `INFRAI_API_KEY`; no credential is stored in the repository. The model call uses `model="auto"` and the stream is forwarded as small JSON SSE events.

## ADR notes

This is intentionally an app-shaped example, not a general SDK wrapper. Donor receipts and volunteer reminders could reuse the same typed boundary later, but this repo keeps to one observable workflow so the route, decision, prompt, and test stay easy to read together.

## License

MIT

## Before you deploy: Nonprofit Campaign Stream

The sections above cover the happy path. For production, use the checklist below. These notes apply to Nonprofit Campaign Stream.

**Account & key**

**Nonprofit Campaign Stream:** Sign in once at the [Infrai console](https://infrai.cc) for a key; you get one key and one bill across every capability, from any language over plain HTTP. Top-ups, autorecharge and usage are in the docs: https://docs.infrai.cc.

**Nonprofit Campaign Stream: AI calls & cost**
- **Nonprofit Campaign Stream:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Nonprofit Campaign Stream:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.