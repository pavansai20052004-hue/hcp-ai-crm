from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import HCP, Interaction


def seed_demo_data(db: Session) -> None:
    if db.query(HCP).first():
        return

    hcps = [
        HCP(
            full_name="Dr. Meera Rao",
            specialty="Cardiology",
            tier="A",
            territory="Hyderabad Central",
            organization="Lotus Heart Institute",
            email="meera.rao@examplehospital.com",
            preferred_channel="Email",
            persona_notes="Evidence-oriented prescriber. Values real-world data and clear access support.",
        ),
        HCP(
            full_name="Dr. Arjun Menon",
            specialty="Endocrinology",
            tier="B",
            territory="Bengaluru East",
            organization="CityCare Diabetes Clinic",
            email="arjun.menon@exampleclinic.com",
            preferred_channel="WhatsApp",
            persona_notes="Time-constrained clinic owner. Prefers concise patient support material.",
        ),
        HCP(
            full_name="Dr. Kavya Iyer",
            specialty="Pulmonology",
            tier="A",
            territory="Chennai South",
            organization="BreatheWell Medical Center",
            email="kavya.iyer@examplecenter.com",
            preferred_channel="In person",
            persona_notes="Collaborative educator. Often asks for peer-led webinars and case studies.",
        ),
    ]
    db.add_all(hcps)
    db.flush()

    db.add(
        Interaction(
            hcp_id=hcps[0].id,
            occurred_at=datetime.now(UTC) - timedelta(days=7),
            channel="In person",
            interaction_type="Detailing",
            summary="Discussed CardioFlow efficacy data and formulary access objections.",
            raw_notes="Dr. Rao asked for more subgroup evidence and wanted a simple payer access sheet.",
            sentiment="Interested",
            topics=["efficacy", "access", "formulary"],
            products=["CardioFlow"],
            objections=["Requested deeper subgroup evidence", "Needs payer access clarity"],
            commitments=["Rep will send payer access sheet", "Rep will schedule data-focused follow-up"],
            compliance_flags=[],
            call_quality_score=86,
            ai_confidence=82,
            follow_up_date=(datetime.now(UTC) + timedelta(days=2)).date().isoformat(),
            follow_up_owner="Field Rep",
            next_best_action="Send the payer access sheet and schedule a data-focused follow-up.",
        )
    )
    db.commit()
