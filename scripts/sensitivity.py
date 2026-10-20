"""Compare trailing references on matched years in the pinned public snapshot.

Run after build.py. Uses only the standard library; never downloads new data.
"""
import hashlib
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
THRESHOLDS = (5, 10, 15, 20)
WINDOWS = (3, 5)
YEARS = tuple(range(2016, 2026))


def trailing_reference(lookup, state_id, year, window):
    history = [lookup.get((state_id, year - lag)) for lag in range(1, window + 1)]
    if any(value is None for value in history):
        return None
    mean = sum(Fraction(str(value)) for value in history) / window
    return mean if mean > 0 else None


def is_shortfall(yield_value, baseline, threshold):
    if yield_value is None or baseline is None or baseline <= 0:
        return None
    # Compare exact decimal inputs before rounding; equality is not an event.
    return Fraction(str(yield_value)) * 100 < (100 - threshold) * baseline


def analyse(rows):
    lookup = {(row['state_id'], row['year']): row['yield_kg_ha'] for row in rows}
    if len(lookup) != len(rows):
        raise ValueError('Duplicate state-year observations')
    names = {row['state_id']: row['state'] for row in rows}
    results = []
    for sid, name in sorted(names.items()):
        evaluated = []
        for year in YEARS:
            value = lookup.get((sid, year))
            references = {str(w): trailing_reference(lookup, sid, year, w) for w in WINDOWS}
            valid = value is not None and all(b is not None for b in references.values())
            evaluated.append({
                'year': year, 'yield_kg_ha': value, 'matched_valid': valid,
                'references': {str(w): {
                    'baseline_kg_ha': float(references[str(w)]) if references[str(w)] is not None else None,
                    'gap_pct': float(100 * (Fraction(str(value)) / references[str(w)] - 1))
                        if value is not None and references[str(w)] is not None else None,
                    'shortfall': {str(t): is_shortfall(value, references[str(w)], t) for t in THRESHOLDS}
                } for w in WINDOWS}
            })
        matched = [row for row in evaluated if row['matched_valid']]
        counts = {str(w): {str(t): sum(row['references'][str(w)]['shortfall'][str(t)] for row in matched)
                          for t in THRESHOLDS} for w in WINDOWS}
        results.append({'state_id': sid, 'state': name, 'n_common': len(matched),
                        'common_years': [row['year'] for row in matched], 'counts': counts,
                        'observations': evaluated})
    return results


def report_html(payload):
    # Every state is retained. Zero valid years is shown as unavailable, not 0%.
    summaries = [{k: row[k] for k in ['state_id', 'state', 'n_common', 'counts']} for row in payload['states']]
    embedded = json.dumps(summaries, ensure_ascii=False).replace('</', '<\\/')
    return '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>How sensitive is a shortfall count? — Edilvando Eufrazio</title>
<style>body{margin:0;background:#F4F0E8;color:#10293D;font:17px/1.6 Arial,Helvetica,sans-serif}main{max-width:1000px;margin:auto;padding:40px 24px}h1{font-size:42px;line-height:1.15}a{color:#007E84}table{border-collapse:collapse;width:100%;background:white}th,td{padding:12px;border-bottom:1px solid #ddd;text-align:left}select{font:inherit;padding:8px}small{display:block;margin:20px 0}.table{overflow:auto}.badge{color:#007E84;font-weight:bold;letter-spacing:2px}.note{border-left:4px solid #007E84;padding:15px;background:white}caption{text-align:left;padding:18px 0}button{font:inherit;padding:8px;cursor:pointer}nav{display:flex;gap:24px;flex-wrap:wrap}</style>
<main><p class="badge">EDILVANDO EUFRAZIO / APPLIED DATA SCIENCE</p>
<nav><a href="index.html">Main dashboard</a><a href="https://github.com/edilvandopereira-dot/crop-yield-risk-explorer">Code and methodology</a></nav>
<h1>Same yields. Different reference.</h1>
<p>Compare shortfall counts using the preceding three-year or five-year arithmetic mean. The evaluation window stays fixed at 2016–2025. Each state uses only years with a valid current yield and both references.</p>
<p class="note">At a 10% threshold, Rio Grande do Sul changes from <strong>3/10</strong> to <strong>4/10</strong> years; Paraná changes from <strong>2/10</strong> to <strong>1/10</strong>. Mato Grosso remains <strong>1/10</strong>. Reference choice changes the description, even with the same observations.</p>
<label for="threshold">Yield strictly more than this percentage below its reference:</label>
<select id="threshold"><option value="5">5%</option><option value="10" selected>10%</option><option value="15">15%</option><option value="20">20%</option></select>
<p id="summary" role="status"></p><button id="download">Download visible comparison JSON</button>
<div class="table"><table><caption>Paired comparison on matched valid years; no minimum area filter</caption><thead><tr><th>State</th><th>Evaluable years</th><th>3-year reference</th><th>5-year reference</th><th>Change in event count</th></tr></thead><tbody id="rows"></tbody></table></div>
<h2>What changes and what stays fixed</h2><p>The reference length and shortfall threshold are separate assumptions. Change one at a time. An event is an annual reported yield strictly below (1 − threshold / 100) × its trailing mean. The reference excludes the current and future years. Missing historical years invalidate that reference. Counts are paired on the intersection of valid years, so the denominator cannot change between the two columns for a state.</p>
<p>States with fewer than five matched valid years are labeled limited coverage. Different states may still have different coverage: inspect denominators before comparing them. This report intentionally retains all 27 states, including those excluded by the main dashboard’s minimum-area filter.</p>
<p>Historical frequencies are descriptive, not forecast probabilities. Longer references can respond more slowly to trends and shocks. Neither reference is established as more accurate by this comparison. State aggregates cannot identify climate causes or select suppliers.</p>
<small>SOURCE: IBGE PAM · SIDRA 1612 · Soybeans (grain). Snapshot: 2026-10-16. No new data downloaded for this extension. <a href="https://sidra.ibge.gov.br/tabela/1612">Official table</a>. <a href="https://github.com/edilvandopereira-dot/crop-yield-risk-explorer/blob/main/analysis/sensitivity_2026-10-20.md">Analysis and validation</a>.</small>
<script>const data=__DATA__;const choice=document.getElementById('threshold');function visible(){return data.map(r=>({state:r.state,evaluable_years:r.n_common,threshold_pct:Number(choice.value),three_year_events:r.n_common?r.counts['3'][choice.value]:null,five_year_events:r.n_common?r.counts['5'][choice.value]:null}));}function render(){const values=visible();document.getElementById('rows').replaceChildren(...values.map(r=>{const tr=document.createElement('tr');const delta=r.evaluable_years?r.five_year_events-r.three_year_events:null;[r.state,r.evaluable_years+(r.evaluable_years<5?' (limited coverage)':''),r.evaluable_years?r.three_year_events+'/'+r.evaluable_years:'Unavailable',r.evaluable_years?r.five_year_events+'/'+r.evaluable_years:'Unavailable',delta===null?'Unavailable':(delta>0?'+':'')+delta].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td)});return tr}));document.getElementById('summary').textContent='27 states retained · '+choice.value+'% threshold · 2016–2025';}choice.addEventListener('change',render);document.getElementById('download').addEventListener('click',()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({source:'IBGE PAM SIDRA 1612',snapshot:'2026-10-16',evaluation:'2016–2025',reference_years:[3,5],comparison:visible()},null,2)],{type:'application/json'}));a.download='soybean-sensitivity-'+choice.value+'pct.json';a.click();URL.revokeObjectURL(a.href)});render();</script></main></html>'''.replace('__DATA__', embedded)


def build_sensitivity():
    source = ROOT / 'data/processed/observations.json'
    data = json.loads(source.read_text())
    result = {'analysis_date': '2026-10-20', 'source_snapshot': data['manifest']['retrieved_at'],
              'input_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'evaluation_years': YEARS, 'reference_lengths': WINDOWS, 'thresholds_pct': THRESHOLDS,
              'comparison': 'Intersection of valid years for both references within each state',
              'states': analyse(data['states'])}
    (ROOT / 'data/processed/sensitivity.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'docs/sensitivity.html').write_text(report_html(result))
    print(json.dumps({'sensitivity_states': len(result['states']), 'snapshot': result['source_snapshot']}))
    return result


if __name__ == '__main__':
    build_sensitivity()
