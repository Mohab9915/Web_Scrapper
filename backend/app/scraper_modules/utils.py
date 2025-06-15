from datetime import datetime
import re
# =============================================================================
# 6) GENERATE UNIQUE FOLDER NAME
# =============================================================================
def generate_unique_name(url: str) -> str:
    """
    Generate a unique name for the folder based on the URL.
    """
    timestamp = datetime.now().strftime('%Y_%m_%d__%H_%M_%S_%f')
    domain = re.sub(r'\W+', '_', url.split('//')[-1].split('/')[0])
    return f"{domain}_{timestamp}"