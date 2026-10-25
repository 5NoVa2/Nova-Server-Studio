"""Distribution identity supplied only by the Store packaging pipeline."""
from pathlib import Path
STORE_BUILD=(Path(__file__).resolve().parent/'store-channel.json').is_file()
