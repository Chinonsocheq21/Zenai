"""Morgan State resources the Resource & Referral specialist can show.

Curated, never generated: the language model does not write phone numbers or
names of offices, because a wrong number in this setting is worse than none.
Every entry was read off morgan.edu on the date in VERIFIED. Re-check them each
semester; offices move.

These are shown as cards beside the reply, only when the student ASKS for help
of that kind. The reply itself stays on protocol (no advice): offering a
resource the student asked for is answering a question, not telling them what
to do.
"""

from __future__ import annotations

VERIFIED = "2026-10-29"

RESOURCES = {
    "counseling": {
        "name": "Counseling Center",
        "what": "Counseling for Morgan students, in person or by phone.",
        "phone": "443-885-3130",
        "detail": "Weekdays 8:30 to 5 · 24/7 line: 1-800-422-0009",
        "url": "https://www.morgan.edu/counselingcenter",
    },
    "tutoring": {
        "name": "Center for Academic Success and Achievement (CASA)",
        "what": "Tutoring and academic advising. Book through Navigate 360.",
        "phone": "443-885-3380",
        "detail": "Tyler Hall, Suite 117 · CASA@morgan.edu",
        "url": "https://www.morgan.edu/tutoring",
    },
    "disability": {
        "name": "Student Disability Support Services",
        "what": "Academic accommodations and disability support.",
        "phone": "443-885-4767",
        "detail": "Richardson Library, Room 133-A · SDSS@morgan.edu",
        "url": "https://www.morgan.edu/sdss",
    },
    "basic_needs": {
        "name": "Food Resource Center",
        "what": "Free groceries and toiletries with your BEARcard, and help applying for SNAP.",
        "phone": "443-885-2736",
        "detail": "McKeldin Center 208 · foodresourcecenter@morgan.edu",
        "url": "https://www.morgan.edu/foodresourcecenter",
    },
    "support": {
        "name": "Student Support and Outreach Services (S.O.S.)",
        "what": "One person who helps you sort out what's getting in the way: money, housing, school or health.",
        "phone": "443-885-4670",
        "detail": "McMechen Hall 634 · sos@morgan.edu",
        "url": "https://www.morgan.edu/student-support-and-outreach",
    },
}


def cards(topics: list[str]) -> list[dict]:
    """The cards for these topics, in order, with S.O.S. as the catch-all."""
    keys = [t for t in topics if t in RESOURCES] or ["support"]
    return [{"id": k, **RESOURCES[k], "verified": VERIFIED} for k in dict.fromkeys(keys)]
