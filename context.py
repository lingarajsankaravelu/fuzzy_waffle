from dataclasses import dataclass, field


# Fixed for the whole session, supplied by the app before the chat starts (stands in
# for a real "fetch user profile from DB" call) — unlike state, nothing in the
# conversation can change these values.
@dataclass
class UserContext:
    name: str
    age: int
    extracurricular_activities: list[str] = field(default_factory=list)
    favourite_dish: str = ""


# Fixed for the whole session — the wedding-level facts sub-agents need (destination
# for travel/venue, guest count for chef/venue, etc.).
@dataclass
class WeddingContext:
    destination: str
    wedding_date: str
    guest_count: int
    budget: str = "not specified"


@dataclass
class PlanningContext:
    user: UserContext
    wedding: WeddingContext


def format_profile(ctx: PlanningContext) -> str:
    user, wedding = ctx.user, ctx.wedding
    return (
        f"You are helping plan a wedding for {user.name} (age {user.age}). "
        f"Their extracurricular activities: {', '.join(user.extracurricular_activities) or 'none noted'}. "
        f"Wedding destination: {wedding.destination}. Date: {wedding.wedding_date}. "
        f"Guest count: {wedding.guest_count}. Budget: {wedding.budget}. "
        "Use these facts to personalize your answer without reciting them back verbatim every message."
    )


# Hardcoded stand-ins for a saved user/wedding profile lookup.
DEFAULT_USER_CONTEXT = UserContext(
    name="John Doe",
    age=30,
    extracurricular_activities=["Badminton", "Pickleball", "GYM", "Walking"],
)

DEFAULT_WEDDING_CONTEXT = WeddingContext(
    destination="Goa, India",
    wedding_date="2026-12-12",
    guest_count=120,
    budget="₹15,00,000",
)

DEFAULT_PLANNING_CONTEXT = PlanningContext(user=DEFAULT_USER_CONTEXT, wedding=DEFAULT_WEDDING_CONTEXT)
