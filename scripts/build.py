"""Validate a pinned source snapshot, derive features in SQL and build offline HTML."""
import hashlib
import json
import math
import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGIONS = {'1': 'North', '2': 'Northeast', '3': 'Southeast', '4': 'South', '5': 'Central-West'}
ABBR = dict(zip(['11','12','13','14','15','16','17','21','22','23','24','25','26','27','28','29','31','32','33','35','41','42','43','50','51','52','53'],
                ['RO','AC','AM','RR','PA','AP','TO','MA','PI','CE','RN','PB','PE','AL','SE','BA','MG','ES','RJ','SP','PR','SC','RS','MS','MT','GO','DF']))
FIELDS = {'109': 'planted_ha', '216': 'harvested_ha', '214': 'production_t', '112': 'reported_yield_kg_ha'}

def numeric(value, variable):
    # SIDRA '-' means absolute zero. A yield with no harvested area is later undefined.
    if value == '-':
        return 0.0
    if value in ('...', '..', 'X', 'x', '', None):
        return None
    try:
        result = float(value)
    except (ValueError, TypeError) as error:
        raise ValueError(f'Unknown SIDRA value {value!r}, variable {variable}') from error
    if not math.isfinite(result) or result < 0:
        raise ValueError(f'Invalid negative/nonfinite value: {value}')
    return result

def parse(raw):
    rows = {}
    symbols = Counter()
    if {v['id'] for v in raw} != set(FIELDS):
        raise ValueError('Expected four known variables.')
    for variable in raw:
        if len(variable['resultados']) != 1:
            raise ValueError('Unexpected classification response.')
        result = variable['resultados'][0]
        categories = result['classificacoes'][0]['categoria']
        if set(categories) != {'2713'}:
            raise ValueError('The source crop is not soybean grain.')
        for series in result['series']:
            loc = series['localidade']
            for year, value in series['serie'].items():
                key = (loc['id'], int(year))
                if not 2010 <= key[1] <= 2025:
                    raise ValueError('Unexpected source year.')
                row = rows.setdefault(key, {'state_id': loc['id'], 'state': loc['nome'], 'year': int(year)})
                field = FIELDS[variable['id']]
                if field in row:
                    raise ValueError('Duplicate state/year/variable.')
                row[field] = numeric(value, variable['id'])
                row.setdefault('source_values', {})[variable['id']] = value
                if value in ('-', '...', '..', 'X', 'x'):
                    symbols[f'{variable["id"]}:{value}'] += 1
    for row in rows.values():
        if not all(f in row for f in FIELDS.values()):
            raise ValueError('Missing source variable.')
        area = row['harvested_ha']
        row['yield_kg_ha'] = row['reported_yield_kg_ha'] if area is not None and area > 0 else None
        row['abbr'] = ABBR.get(row['state_id'], 'BR')
        row['region'] = REGIONS.get(row['state_id'][0], 'Brazil') if row['state_id'] != '1' else 'Brazil'
    return sorted(rows.values(), key=lambda r: (r['state_id'], r['year'])), dict(symbols)

def add_baselines(rows):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE observations(state_id TEXT,year INTEGER,yield_kg_ha REAL,PRIMARY KEY(state_id,year))')
    db.executemany('INSERT INTO observations VALUES (?,?,?)',
                   [(r['state_id'],r['year'],r['yield_kg_ha']) for r in rows])
    baselines = {(sid, year): baseline for sid, year, _, baseline in db.execute((ROOT/'sql/rolling_baseline.sql').read_text())}
    for r in rows:
        r['baseline_kg_ha'] = baselines[(r['state_id'], r['year'])]
        b, y = r['baseline_kg_ha'], r['yield_kg_ha']
        r['gap_pct'] = 100 * (y / b - 1) if b is not None and b > 0 and y is not None else None
    db.close()

def build():
    raw = ROOT/'data/raw'
    manifest = json.loads((raw/'manifest.json').read_text())
    for entry in manifest['files']:
        if hashlib.sha256((raw/entry['file']).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Source hash mismatch: '+entry['file'])
    states, state_symbols = parse(json.loads((raw/'states.json').read_text()))
    brazil, brazil_symbols = parse(json.loads((raw/'brazil.json').read_text()))
    if len(states) != 27 * 16 or len(brazil) != 16:
        raise ValueError('Expected a complete 27-state × 16-year grid plus national observations.')
    add_baselines(states)
    add_baselines(brazil)
    # Compare additive measures at the same geographic level. Never sum state yields.
    reconciliation = []
    for national in brazil:
        members = [r for r in states if r['year'] == national['year']]
        for f in ['planted_ha','harvested_ha','production_t']:
            values = [r[f] for r in members]
            total = sum(v for v in values if v is not None)
            expected = national[f]
            diff = total - expected if expected is not None else None
            reconciliation.append({'year': national['year'], 'field': f, 'state_sum': total,
                                   'national': expected, 'difference': diff,
                                   'missing_states': sum(v is None for v in values)})
    failures = [r for r in reconciliation if r['difference'] != 0 or r['missing_states']]
    ratio_checks = []
    for row in states + brazil:
        if row['harvested_ha'] and row['production_t'] is not None and row['yield_kg_ha'] is not None:
            diff = row['yield_kg_ha'] - row['production_t']*1000/row['harvested_ha']
            if abs(diff) > 2:
                ratio_checks.append({'state': row['state'], 'year': row['year'], 'difference_kg_ha': diff})
    qa = {'hashes_verified': len(manifest['files']), 'state_year_rows': len(states),
          'national_rows': len(brazil), 'symbols': state_symbols,
          'national_symbols': brazil_symbols, 'undefined_yield_rows': sum(r['yield_kg_ha'] is None for r in states),
          'aggregate_reconciliation': reconciliation, 'aggregate_discrepancies': failures,
          'yield_ratio_discrepancies_over_2_kg_ha': ratio_checks,
          'passed': not failures and not ratio_checks}
    if not qa['passed']:
        # Keep evidence and fail before making a dashboard with unchecked source assumptions.
        (ROOT/'data/qa.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
        raise ValueError('Source consistency checks need review; see data/qa.json')
    payload = {'states': states, 'brazil': brazil, 'manifest': manifest,
               'latest_year': max(r['year'] for r in brazil),
               'table_url': 'https://sidra.ibge.gov.br/tabela/1612',
               'evaluation': 'Current-vintage retrospective analysis, not an as-of-release forecast backtest.'}
    out = ROOT/'data/processed'; out.mkdir(parents=True,exist_ok=True)
    (out/'observations.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'data/qa.json').write_text(json.dumps(qa,indent=2),encoding='utf-8')
    template = (ROOT/'web/template.html').read_text(encoding='utf-8')
    content = template.replace('__STYLE__',(ROOT/'web/style.css').read_text())
    content = content.replace('__CHARTJS__',(ROOT/'vendor/chart.umd.min.js').read_text())
    content = content.replace('__DATA__',json.dumps(payload,ensure_ascii=False).replace('</','<\\/'))
    content = content.replace('__APP__',(ROOT/'web/app.js').read_text())
    docs = ROOT/'docs'; docs.mkdir(exist_ok=True)
    (docs/'index.html').write_text(content,encoding='utf-8')
    print(json.dumps({'dashboard':'docs/index.html','rows':len(states),'latest_year':payload['latest_year'],
                      'national_production_t':brazil[-1]['production_t'],'qa_passed':qa['passed']},indent=2))
    return payload

if __name__ == '__main__':
    build()
