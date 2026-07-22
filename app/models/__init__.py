"""Model registry.

Importing this package imports every model module so SQLAlchemy's metadata
is fully populated before ``db.create_all()`` runs in the app factory.
"""

from app.models.ai_generation_model import AIGeneration
from app.models.analytics_snapshot_model import AnalyticsSnapshot
from app.models.credit_usage_model import CreditUsage
from app.models.notification_model import Notification
from app.models.referral_model import Referral
from app.models.scheduled_post_model import ScheduledPost
from app.models.social_account_model import SocialAccount
from app.models.subscription_model import Subscription
from app.models.user_model import User
from app.models.workspace_member_model import WorkspaceMember
from app.models.workspace_model import Workspace

__all__ = [
    "User",
    "Workspace",
    "WorkspaceMember",
    "SocialAccount",
    "AnalyticsSnapshot",
    "AIGeneration",
    "ScheduledPost",
    "Subscription",
    "CreditUsage",
    "Notification",
    "Referral",
]
