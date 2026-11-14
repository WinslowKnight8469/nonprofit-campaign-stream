from src.nonprofit_stream import CampaignReportRequest, decide_campaign


def test_reached_goal_routes_to_donor_thanks():
    request = CampaignReportRequest(
        campaign_name="Warm Meals",
        donor_count=18,
        volunteer_hours=42,
        goal_amount=1000,
        raised_amount=1000,
    )

    assert decide_campaign(request).model_dump() == {
        "status": "goal_reached",
        "next_step": "thank_donors",
    }

