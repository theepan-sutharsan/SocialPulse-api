"""Seed / demo data script.

Run with:  python seed.py

Creates the SocialBlade-style demo so the connect -> snapshot -> chart ->
generate flow works out of the box (spec §19):

* 1 platform admin
* Asha (Pro) — YouTube (live-shaped) + Instagram (Demo Mode)
* Rahul (Agency) — owns an agency workspace + 2 client workspaces (many-to-many)
* 30 days of backfilled analytics snapshots per connected account
* 1 AI generation, 1 scheduled post, partially-consumed credit ledgers
"""

from datetime import timedelta

from app import create_app
from app.controllers.credit_usage_controller import get_or_create_current_usage
from app.extensions import db
from app.models.ai_generation_model import AIGeneration
from app.models.notification_model import Notification
from app.models.scheduled_post_model import ScheduledPost
from app.models.social_account_model import SocialAccount
from app.models.subscription_model import Subscription
from app.models.user_model import User
from app.models.workspace_member_model import WorkspaceMember
from app.models.workspace_model import Workspace
from app.services import snapshot_service
from app.utils import utc_now

app = create_app()


def _member(user, workspace, role):
    return WorkspaceMember(
        user_id=user.id, workspace_id=workspace.id, role=role, joined_at=utc_now()
    )


def _subscription(workspace, provider=None):
    return Subscription(
        workspace_id=workspace.id,
        plan_tier=workspace.plan_tier,
        status="active",
        billing_provider=provider,
        current_period_end=utc_now() + timedelta(days=30),
    )


def seed():
    with app.app_context():
        db.create_all()

        if User.query.filter_by(email="admin@saasapp.test").first():
            print("Database already seeded. Skipping.")
            return

        # --- Platform admin ---
        admin = User(
            email="admin@saasapp.test",
            full_name="Platform Admin",
            is_platform_admin=True,
        )
        admin.set_password("Admin123")
        db.session.add(admin)

        # --- Asha (Pro creator) ---
        asha = User(email="asha@saasapp.test", full_name="Asha")
        asha.set_password("Password123")
        db.session.add(asha)
        db.session.flush()

        asha_ws = Workspace(name="Asha Creates", slug="asha-creates", plan_tier="pro")
        db.session.add(asha_ws)
        db.session.flush()
        db.session.add(_member(asha, asha_ws, "owner"))
        db.session.add(_subscription(asha_ws, provider="stripe"))

        yt = SocialAccount(
            workspace_id=asha_ws.id,
            platform="youtube",
            handle="Asha Creates",
            is_demo=False,
            connected_at=utc_now(),
        )
        ig = SocialAccount(
            workspace_id=asha_ws.id,
            platform="instagram",
            handle="@ashacreates",
            is_demo=True,
        )
        db.session.add_all([yt, ig])

        # --- Rahul (Agency, manages multiple client workspaces) ---
        rahul = User(email="rahul@saasapp.test", full_name="Rahul")
        rahul.set_password("Password123")
        db.session.add(rahul)
        db.session.flush()

        rahul_ws = Workspace(
            name="Rahul Agency", slug="rahul-agency", plan_tier="agency", is_agency=True
        )
        client_one = Workspace(name="Client One", slug="client-one", plan_tier="pro")
        client_two = Workspace(name="Client Two", slug="client-two", plan_tier="free")
        db.session.add_all([rahul_ws, client_one, client_two])
        db.session.flush()

        # SIGNATURE many-to-many: one user, several workspaces, different roles.
        db.session.add_all(
            [
                _member(rahul, rahul_ws, "owner"),
                _member(rahul, client_one, "owner"),
                _member(rahul, client_two, "editor"),
                _subscription(rahul_ws, provider="razorpay"),
                _subscription(client_one),
                _subscription(client_two),
            ]
        )
        db.session.add_all(
            [
                SocialAccount(
                    workspace_id=client_one.id,
                    platform="youtube",
                    handle="Client One",
                    is_demo=False,
                    connected_at=utc_now(),
                ),
                SocialAccount(
                    workspace_id=client_one.id,
                    platform="tiktok",
                    handle="@clientone",
                    is_demo=True,
                ),
                SocialAccount(
                    workspace_id=client_two.id,
                    platform="twitter",
                    handle="@clienttwo",
                    is_demo=True,
                ),
            ]
        )
        db.session.commit()

        # --- 30 days of backfilled snapshots per account ---
        for account in SocialAccount.query.all():
            snapshot_service.backfill_account(account, days=30)

        # --- Partially-consumed credit ledgers ---
        for workspace, used in [
            (asha_ws, 42),
            (rahul_ws, 120),
            (client_one, 30),
            (client_two, 2),
        ]:
            usage = get_or_create_current_usage(workspace)
            usage.credits_used = min(used, usage.credits_allotted)
        db.session.commit()

        # --- 1 completed AI generation for Asha ---
        generation = AIGeneration(
            workspace_id=asha_ws.id,
            social_account_id=yt.id,
            generation_type="caption",
            prompt_input="Topic: New reel dropping tomorrow\nPlatform: instagram\nTone: engaging",
            result="New reel drops tomorrow and you are NOT ready. Save this so you don't miss it.",
            provider="local-fallback",
            credits_used=1,
        )
        db.session.add(generation)
        db.session.flush()

        # --- 1 scheduled post (~2 days ahead) ---
        db.session.add(
            ScheduledPost(
                workspace_id=asha_ws.id,
                ai_generation_id=generation.id,
                social_account_id=ig.id,
                caption="New reel drops tomorrow — save this!",
                scheduled_at=utc_now() + timedelta(days=2),
                status="planned",
            )
        )
        db.session.add(
            Notification(
                user_id=asha.id,
                workspace_id=asha_ws.id,
                type="milestone",
                message="Your YouTube channel just crossed a new subscriber milestone!",
            )
        )
        db.session.commit()

        print("Seed complete. Demo logins:")
        print("  Platform admin : admin@saasapp.test / Admin123")
        print("  Asha (Pro)     : asha@saasapp.test  / Password123")
        print("  Rahul (Agency) : rahul@saasapp.test / Password123")


if __name__ == "__main__":
    seed()
