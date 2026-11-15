# Inputs: JSON request bodies, query values, and decoded D1 rows conforming to frontend/src/shared/types.ts.
# Outputs: validated Pydantic request, response, and enum types with exact frontend field names and nullable fields.
# Explanation: Defines the backend wire contract in small domain-specific schema modules.
from .models_common import *
from .models_auth import *
from .models_research import *
from .models_outreach import *
from .models_bookings import *
from .models_dashboard import *
