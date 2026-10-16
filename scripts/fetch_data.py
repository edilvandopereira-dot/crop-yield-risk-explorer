"""Download the official IBGE PAM snapshot. No credentials or personal data."""
import hashlib
import gzip
import json
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
BASE = 'https://servicodados.ibge.gov.br/api/v3/agregados/1612'
SOURCES = {
    'metadata.json': BASE + '/metadados',
    'periods.json': BASE + '/periodos',
    'states.json': BASE + '/periodos/2010-2025/variaveis/109%7C216%7C214%7C112?localidades=N3%5Ball%5D&classificacao=81%5B2713%5D',
    'brazil.json': BASE + '/periodos/2010-2025/variaveis/109%7C216%7C214%7C112?localidades=N1%5Ball%5D&classificacao=81%5B2713%5D',
}

def fetch():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {'retrieved_at': datetime.now(timezone.utc).isoformat(), 'table': 1612,
                'classification': 81, 'category': 2713, 'crop': 'Soybeans (grain)',
                'requested_years': [2010, 2025], 'files': []}
    for name, url in SOURCES.items():
        request = Request(url, headers={'User-Agent': 'CropYieldRiskPortfolio/1.0'})
        with urlopen(request, timeout=60) as response:
            content = response.read()
        if content[:2] == b'\x1f\x8b':
            content = gzip.decompress(content)
        parsed = json.loads(content)
        if not isinstance(parsed, (list, dict)) or not parsed:
            raise ValueError(f'Unexpected source response: {name}')
        (RAW / name).write_bytes(content)
        manifest['files'].append({'file': name, 'url': url, 'bytes': len(content),
                                  'sha256': hashlib.sha256(content).hexdigest()})
    (RAW / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Downloaded {len(SOURCES)} official IBGE source files.')

if __name__ == '__main__':
    fetch()
