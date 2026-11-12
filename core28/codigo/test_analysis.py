import unittest
from copy import deepcopy
from analysis_core import aggregate_logic, summarize, union_cells, registry_conjunction, compact, applicable, MODS, COMPS

def cell(state='unknown',kind=None,u='u1',m=MODS[0],reg='NCT1'):
    return dict(state=state,proof_kind=kind,unit_id=u,registry_id=reg,trial=u,program='P',
        reference_id='R',component='suicide_death',modality=m,judgment_ids=[u+m],baseline_state=state)

class TestDocumentaryAnalysis(unittest.TestCase):
    def test_unknown_is_not_negative(self):
        r=summarize([cell()],'x')[0];self.assertEqual((r['complete'],r['unknown'],r['bounded_not_complete']),(0,1,0))
        self.assertEqual((r['identification_lower'],r['identification_upper']),(0,1))
    def test_mixed_denominator_keeps_unknown(self):
        r=summarize([cell('complete','direct'),cell(u='u2'),cell('bounded_not_complete',u='u3')],'x')[0]
        self.assertEqual((r['N'],r['identification_lower'],r['identification_upper']),(3,1/3,2/3))
    def test_all_positive_interval_point(self):
        r=summarize([cell('complete','derived')],'x')[0];self.assertEqual((r['identification_lower'],r['identification_upper']),(1,1))
    def test_all_negative_interval_point(self):
        r=summarize([cell('bounded_not_complete')],'x')[0];self.assertEqual((r['identification_lower'],r['identification_upper']),(0,0))
    def test_na_has_no_interval(self):
        r=summarize([cell('not_applicable')],'x')[0];self.assertEqual(r['N'],0);self.assertIsNone(r['identification_upper'])
    def test_na_does_not_become_unknown(self):
        r=summarize([cell('not_applicable')],'x')[0];self.assertEqual((r['unknown'],r['not_applicable']),(0,1))
    def test_duplicate_population_rejected(self):
        with self.assertRaises(AssertionError):summarize([cell(),cell()],'x')
    def test_union_complete_survives_unknown(self):
        self.assertEqual(aggregate_logic([cell('complete','derived'),cell()],'any'),('complete','derived'))
    def test_union_negative_does_not_cancel_unknown(self):
        self.assertEqual(aggregate_logic([cell('bounded_not_complete'),cell()],'any')[0],'unknown')
    def test_union_all_negative(self):
        self.assertEqual(aggregate_logic([cell('bounded_not_complete')]*2,'any')[0],'bounded_not_complete')
    def test_union_direct_supported_overlaps_derived(self):
        self.assertEqual(aggregate_logic([cell('complete','derived'),cell('complete','direct')],'any'),('complete','direct'))
    def test_union_deduplicates_modality_witnesses(self):
        rs=union_cells([cell('complete','direct'),cell('complete','derived',m=MODS[2])]);self.assertEqual(len(rs),1)
        self.assertEqual(summarize(rs,'x')[0]['complete'],1)
    def test_conjunction_requires_both_populations(self):
        self.assertEqual(aggregate_logic([cell('complete','direct'),cell()],'all')[0],'unknown')
    def test_conjunction_negative_is_definitive(self):
        self.assertEqual(aggregate_logic([cell('bounded_not_complete'),cell()],'all')[0],'bounded_not_complete')
    def test_conjunction_mixed_requires_derivation(self):
        self.assertEqual(aggregate_logic([cell('complete','direct'),cell('complete','derived')],'all'),('complete','derived'))
    def test_osa_not_counted_as_two_registries(self):
        r=registry_conjunction([cell('complete','direct'),cell('complete','derived',u='u2')]);self.assertEqual(len(r),1)
    def test_different_registry_not_merged(self):
        self.assertEqual(len(registry_conjunction([cell(),cell(u='u2',reg='NCT2')])),2)
    def test_union_then_registry_order(self):
        rs=[cell('complete','direct',m=MODS[0]),cell(m=MODS[1]),cell(u='u2',m=MODS[0]),cell('complete','direct',u='u2',m=MODS[1])]
        self.assertEqual(registry_conjunction(union_cells(rs))[0]['state'],'complete')
        self.assertEqual(union_cells(registry_conjunction(rs))[0]['state'],'unknown')
    def test_mortality_not_applicable_to_ideation(self):self.assertFalse(applicable(COMPS[0],MODS[2]))
    def test_mortality_not_applicable_to_attempt(self):self.assertFalse(applicable(COMPS[1],MODS[2]))
    def test_mortality_applicable_to_death(self):self.assertTrue(applicable(COMPS[2],MODS[2]))
    def test_unknown_kept_under_proof_withdrawal(self):
        raw=dict(unit_id='u1',trial='T',reference_id='R',component='C',modality='M',judgment_id='J',analytical_state='unknown',source_scoped_status='reference_unverifiable')
        self.assertEqual(compact(raw,dict(registry_id='N',trial='T',program='P'),True)['state'],'unknown')
    def test_derived_withdrawal_does_not_mutate_input(self):
        raw=dict(unit_id='u1',trial='T',reference_id='R',component='C',modality='M',judgment_id='J',analytical_state='complete',source_scoped_status='complete_derived')
        before=deepcopy(raw);r=compact(raw,dict(registry_id='N',trial='T',program='P'),True)
        self.assertEqual(r['state'],'unknown');self.assertTrue(r['derived_proof_withheld']);self.assertEqual(raw,before)
    def test_direct_not_withdrawn(self):
        raw=dict(unit_id='u1',trial='T',reference_id='R',component='C',modality='M',judgment_id='J',analytical_state='complete',source_scoped_status='complete_direct')
        self.assertEqual(compact(raw,dict(registry_id='N',trial='T',program='P'),True)['state'],'complete')
    def test_withheld_unknown_separately_counted(self):
        a=cell();a['baseline_state']='complete';r=summarize([a,cell(u='u2')],'x')[0]
        self.assertEqual((r['unknown'],r['unknown_introduced_by_proof_withholding']),(2,1))
    def test_na_ignored_in_union(self):
        self.assertEqual(aggregate_logic([cell('not_applicable'),cell('bounded_not_complete')],'any')[0],'bounded_not_complete')
    def test_no_evidence_not_a_complete_union(self):self.assertEqual(aggregate_logic([],'any')[0],'not_applicable')
    def test_derived_ae_not_removed_with_mortality(self):
        r=union_cells([cell('complete','derived'),cell('complete','derived',m=MODS[2])],MODS[:2])[0]
        self.assertEqual((r['state'],r['proof_kind']),('complete','derived'))

if __name__=='__main__':unittest.main()
