"""Export the baseline-sensitivity story from validated, matched-year counts."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
payload = json.loads((ROOT/'data/processed/sensitivity.json').read_text())
by_id = {r['state_id']: r for r in payload['states']}
selected = [by_id[sid] for sid in ['51', '43', '41', '52']]
ink, teal, copper, paper, muted = '#10293D', '#007E84', '#C26642', '#F4F0E8', '#596C77'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':ink,'axes.labelcolor':ink,
                     'xtick.color':muted,'ytick.color':muted,'svg.fonttype':'none','font.size':12})
fig = plt.figure(figsize=(10,11.25), dpi=120, facecolor=paper)
fig.text(.075,.947,'EDILVANDO EUFRAZIO     /     APPLIED DATA SCIENCE',color=teal,fontsize=10,weight='bold')
fig.text(.075,.885,'Same yields.\nDifferent shortfall counts.',fontsize=30,weight='bold',va='top',linespacing=1.2)
fig.text(.075,.755,'Years with yield strictly more than 10% below its reference.\nSame evaluation window: 2016–2025. Same 10 valid years.',color=muted,fontsize=13,va='top',linespacing=1.6)
ax = fig.add_axes([.27,.345,.59,.30],facecolor=paper)
for i, r in enumerate(selected):
    for offset,w,c in [(-.17,'3',teal),(.17,'5',copper)]:
        value=r['counts'][w]['10']
        ax.barh(i+offset,value,height=.27,color=c,label=f'Preceding {w}-year mean' if i==0 else None)
        ax.text(value+.09,i+offset,f"{value} / {r['n_common']}",color=ink,va='center',fontsize=13,weight='bold')
ax.set_yticks(range(4),[r['state'] for r in selected],fontsize=12)
ax.set_xlim(0,5);ax.set_xticks(range(6));ax.invert_yaxis()
ax.set_xlabel('Shortfall years out of 10',labelpad=12)
ax.legend(frameon=False,loc='lower left',bbox_to_anchor=(-.34,1.00),fontsize=12)
for spine in ax.spines.values():spine.set_visible(False)
ax.tick_params(axis='y',length=0,pad=12)
ax.set_axisbelow(True);ax.grid(axis='x',alpha=.15)
rs=by_id['43']; row=next(r for r in rs['observations'] if r['year']==2025)
fig.text(.075,.245,'The reference changes the classification.',color=teal,fontsize=17,weight='bold')
fig.text(.075,.188,'Rio Grande do Sul, 2025: '+f"{row['references']['3']['gap_pct']:.1f}% vs. the 3-year mean;\n{row['references']['5']['gap_pct']:.1f}% vs. the 5-year mean.",fontsize=13,color=ink,linespacing=1.6)
fig.text(.075,.102,'Neither reference is proven more accurate by this comparison.\nHistorical counts are descriptive, not forecast probabilities.',fontsize=11,linespacing=1.5)
fig.text(.075,.040,'SOURCE  IBGE PAM · SIDRA 1612 · Soybeans (grain)\nSnapshot: 2026-10-16 · State aggregates · Matched valid years',fontsize=9,color=muted,linespacing=1.5)
for ext in ['png','svg']:
    fig.savefig(ROOT/f'assets/baseline-sensitivity-2026-10-20.{ext}',facecolor=paper)
print('Exported baseline sensitivity figure (1200 × 1350)')
