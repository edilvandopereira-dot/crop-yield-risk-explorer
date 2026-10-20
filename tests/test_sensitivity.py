"""Protect paired denominators, chronological references and threshold semantics."""
import importlib.util
import json
import sqlite3
from fractions import Fraction
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sensitivity', ROOT / 'scripts/sensitivity.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class SensitivitySemantics(unittest.TestCase):
    def test_snapshot_matches_independent_sql_windows(self):
        data = json.loads((ROOT/'data/processed/observations.json').read_text())
        result = module.analyse(data['states'])
        db = sqlite3.connect(':memory:')
        db.execute('create table obs(sid text, year int, yield real)')
        db.executemany('insert into obs values (?,?,?)',
                      [(r['state_id'],r['year'],r['yield_kg_ha']) for r in data['states']])
        sql = '''with refs as (select sid,year,yield,
          case when count(yield) over w3=3 then avg(yield) over w3 end b3,
          case when count(yield) over w5=5 then avg(yield) over w5 end b5
          from obs window w3 as(partition by sid order by year rows between 3 preceding and 1 preceding),
          w5 as(partition by sid order by year rows between 5 preceding and 1 preceding))
          select sid,year,yield,b3,b5 from refs where year between 2016 and 2025'''
        independent = list(db.execute(sql))
        checks = 0
        for state in result:
            matched = [r for r in independent if r[0]==state['state_id'] and
                       r[2] is not None and r[3] is not None and r[3]>0 and r[4] is not None and r[4]>0]
            self.assertEqual(state['common_years'], [r[1] for r in matched])
            for w, index in [('3',3),('5',4)]:
                for threshold in module.THRESHOLDS:
                    count = sum(100*r[2] < (100-threshold)*r[index] for r in matched)
                    self.assertEqual(count,state['counts'][w][str(threshold)])
                    checks += 1
        self.assertEqual(checks,216)
        db.close()

    def test_strict_threshold_does_not_classify_equality(self):
        self.assertFalse(module.is_shortfall(850, Fraction(1000), 15))
        self.assertTrue(module.is_shortfall(849, Fraction(1000), 15))
        self.assertFalse(module.is_shortfall(851, Fraction(1000), 15))

    def test_reference_uses_exact_consecutive_past_years(self):
        values = {('51', 2010+i): 1000 for i in range(7)}
        values[('51', 2016)] = 90000
        values[('43', 2015)] = 50000
        self.assertEqual(module.trailing_reference(values, '51', 2016, 5), 1000)
        values[('51', 2012)] = None
        self.assertIsNone(module.trailing_reference(values, '51', 2016, 5))
        self.assertEqual(module.trailing_reference(values, '51', 2016, 3), 1000)

    def test_comparison_pairs_denominators_and_retains_empty_states(self):
        rows = [{'state_id': sid, 'state': sid, 'year': y, 'yield_kg_ha':
                 (None if sid == '43' or y == 2012 else 1000)}
                for sid in ['51', '43'] for y in range(2010, 2026)]
        result = module.analyse(rows)
        by_id = {r['state_id']: r for r in result}
        self.assertEqual(by_id['51']['n_common'], 8)
        self.assertNotIn(2016, by_id['51']['common_years'])
        self.assertNotIn(2017, by_id['51']['common_years'])
        self.assertEqual(by_id['43']['n_common'], 0)


if __name__ == '__main__':
    unittest.main()
