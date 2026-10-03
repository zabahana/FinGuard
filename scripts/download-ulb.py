"""Download the original ULB CSV from Kaggle and verify the known source checksum."""
import hashlib
from pathlib import Path
import shutil
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

URL = "https://www.kaggle.com/api/v1/datasets/download/mlg-ulb/creditcardfraud"
EXPECTED = "76274b691b16a6c49d3f159c883398e03ccd6d1ee12d9d8ee38f4b4b98551a89"
destination = Path(__file__).resolve().parents[1] / ".local/datasets/ulb"
destination.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=destination) as temporary:
    archive = Path(temporary) / "download.zip"
    with urlopen(URL, timeout=120) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)
    csv_path = Path(temporary) / "creditcard.csv"
    with ZipFile(archive) as dataset, dataset.open("creditcard.csv") as source, csv_path.open("wb") as output:
        shutil.copyfileobj(source, output)
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if digest != EXPECTED:
        raise SystemExit("Dataset checksum changed; original CSV preserved. Verify the new source before using it.")
    csv_path.replace(destination / "creditcard.csv")
print(f"Verified ULB dataset: {destination / 'creditcard.csv'}")
