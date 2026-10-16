"""Create a LinkedIn figure directly from the validated IBGE snapshot."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/processed/observations.json').read_text())
ink='#10293D';teal='#007E84';copper='#C26642';paper='#F4F0E8';muted='#596C77'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':ink,'axes.labelcolor':ink,
 'xtick.color':muted,'ytick.color':muted,'svg.fonttype':'none','font.size':12})
f=plt.figure(figsize=(10,11.25),dpi=120,facecolor=paper)
f.text(.075,.948,'EDILVANDO EUFRAZIO     /     APPLIED DATA SCIENCE',fontsize=10,color=teal,weight='bold')
f.text(.075,.887,'Two major soybean states.\nDifferent downside histories.',fontsize=28,weight='bold',va='top',linespacing=1.25)
f.text(.075,.755,'Annual yield relative to each state’s preceding three-year mean.\nOfficial IBGE data. Evaluation window: 2016–2025.',fontsize=13,color=muted,va='top',linespacing=1.6)
ax=f.add_axes([.12,.365,.78,.30],facecolor=paper)
summary=[]
for sid,c,marker in [('51',teal,'o'),('43',copper,'s')]:
 rows=[r for r in data['states'] if r['state_id']==sid and 2016<=r['year']<=2025]
 valid=[r for r in rows if r['gap_pct'] is not None]
 count=sum(r['gap_pct'] < -10 for r in valid)
 worst=min(r['gap_pct'] for r in valid)
 ax.plot([r['year'] for r in rows],[r['gap_pct'] for r in rows],label=rows[0]['state'],color=c,marker=marker,lw=2.8,ms=5)
 summary.append({'state':rows[0]['state'],'count':count,'n':len(valid),'worst':worst,'production':rows[-1]['production_t'],'color':c})
ax.axhline(0,color='#8B9D9E',lw=1)
ax.axhline(-10,color=ink,ls=(0,(5,4)),lw=1.3)
ax.text(2025.1,-10,'−10%',va='center',fontsize=10,color=ink)
ax.set_xlim(2015.7,2026.2);ax.set_ylim(-55,35)
ax.set_xticks([2016,2018,2020,2022,2024]);ax.set_xlabel('Year',labelpad=12)
ax.set_yticks([-50,-25,0,25],['−50%','−25%','0%','+25%'])
ax.set_ylabel('Gap to preceding three-year mean',labelpad=12,fontsize=11)
for spine in ax.spines.values():spine.set_visible(False)
ax.grid(axis='y',alpha=.15)
ax.legend(frameon=False,loc='lower left',bbox_to_anchor=(0,1.04),ncol=2,fontsize=12)
for x,s in zip([.075,.54],summary):
 f.text(x,.265,s['state'],fontsize=16,weight='bold',color=s['color'])
 f.text(x,.209,f"{s['count']} / {s['n']} years",fontsize=25,weight='bold',color=s['color'])
 f.text(x,.157,f"Yield more than 10% below baseline\nWorst gap: {s['worst']:.1f}%",fontsize=12,color=muted,linespacing=1.6)
f.text(.075,.095,'Historical frequency is descriptive. It does not predict next year’s harvest.',fontsize=11,color=ink)
f.text(.075,.047,'SOURCE  IBGE PAM · SIDRA 1612 · Soybeans (grain)\nSnapshot: '+data['manifest']['retrieved_at'][:10]+' · State averages; no causal attribution',fontsize=9,color=muted,linespacing=1.5)
for ext in ['png','svg']:
 f.savefig(ROOT/f'assets/yield-shortfalls.{ext}',facecolor=paper)
print(json.dumps(summary,indent=2))
