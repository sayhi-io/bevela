import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from project_intent.workspace_inventory import observe


class WorkspaceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        for name in ('connected','missing','private'):
            (self.root/name/'.git').mkdir(parents=True)
        (self.root/'not-a-repo').mkdir()
        (self.root/'linked').symlink_to(self.root/'connected',target_is_directory=True)
        self.config={'workspace_inventory':{'root':str(self.root),'scope_by_repository':{'connected':'scope/a','private':'scope/private'}}}
        self.principal={'workspace_inventory':True,'scopes':['scope/a']}
        self.projection={'scopes':[{'id':'scope/a','provider_status':'live','execution':{'status':'not-connected'}}],
                         'workstreams':[{'scope_id':'scope/a','id':'one'}]}

    def test_opt_in_checked_before_filesystem(self):
        with patch('os.scandir',side_effect=AssertionError('must not scan')):
            self.assertIsNone(observe(self.config,{'scopes':['scope/a']},self.projection))

    def test_inventory_gaps_and_scope_isolation(self):
        value=observe(self.config,self.principal,self.projection)
        self.assertEqual([r['repository'] for r in value['repositories']],['connected','missing'])
        self.assertEqual(value['connected_count'],1)
        self.assertIsNone(value['repositories'][1]['enrolled_workstreams'])
        self.assertEqual(value['repositories'][1]['intent_status'],'not-mapped')
        selected=observe(self.config,self.principal,self.projection,'scope/a')
        self.assertEqual([r['repository'] for r in selected['repositories']],['connected'])

    def test_unavailable_not_empty_success(self):
        self.config['workspace_inventory']['root']=str(self.root/'absent')
        result=observe(self.config,self.principal,self.projection)
        self.assertEqual(result['status'],'unavailable')

    def test_enumeration_bound_visible(self):
        for i in range(201):(self.root/str(i)).mkdir()
        result=observe(self.config,self.principal,self.projection)
        self.assertEqual(result['status'],'partial-limit')
