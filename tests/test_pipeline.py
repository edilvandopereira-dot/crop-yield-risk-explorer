"""Tests for analytical semantics that can silently change a business conclusion."""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('build',ROOT/'scripts/build.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class AnalyticalSemantics(unittest.TestCase):
    def test_rolling_baseline_excludes_current_and_future(self):
        rows = [{'state_id':'51','year':2010+i,'yield_kg_ha':y} for i,y in enumerate([1000,2000,3000,9000,50000])]
        module.add_baselines(rows)
        self.assertEqual(rows[3]['baseline_kg_ha'],2000)
        self.assertEqual(rows[4]['baseline_kg_ha'],14000/3)
        self.assertIsNone(rows[2]['baseline_kg_ha'])

    def test_missing_preceding_year_is_not_skipped(self):
        rows = [{'state_id':'51','year':2010+i,'yield_kg_ha':y} for i,y in enumerate([1000,None,3000,2000])]
        module.add_baselines(rows)
        self.assertIsNone(rows[-1]['baseline_kg_ha'])
        self.assertIsNone(rows[-1]['gap_pct'])

    def test_states_never_share_a_baseline(self):
        rows = [{'state_id':sid,'year':2010+i,'yield_kg_ha':y} for sid,y in [('51',1000),('43',5000)] for i in range(4)]
        module.add_baselines(rows)
        self.assertEqual(rows[3]['baseline_kg_ha'],1000)
        self.assertEqual(rows[7]['baseline_kg_ha'],5000)

    def test_sidra_symbols_preserve_zero_and_missing(self):
        self.assertEqual(module.numeric('-',214),0)
        for x in ['...','..','X',None]: self.assertIsNone(module.numeric(x,214))
        with self.assertRaises(ValueError): module.numeric('unexpected',214)

if __name__ == '__main__': unittest.main()
