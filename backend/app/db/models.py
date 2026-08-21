"""Import all persistence models so Alembic can discover their metadata."""

from app.modules.brands.model import Brand
from app.modules.competitors.model import Competitor
from app.modules.creatives.model import Creative, CreativeAnalysis, CreativeAsset
from app.modules.ingestion.model import CollectionSource
from app.modules.jobs.model import Job
from app.modules.organizations.model import Membership, Organization
from app.modules.usage.model import ApiUsage
from app.modules.users.model import User

__all__ = [
    "ApiUsage",
    "Brand",
    "Competitor",
    "Creative",
    "CreativeAnalysis",
    "CreativeAsset",
    "CollectionSource",
    "Job",
    "Membership",
    "Organization",
    "User",
]
