"""
Test for DBCaseRecorders.
"""

import unittest
import tempfile
import StringIO
import os
import tempfile
import logging
import shutil

from openmdao.main.api import Component, Assembly, Case, set_as_top
from openmdao.test.execcomp import ExecComp
from openmdao.lib.caseiterators.api import DBCaseIterator, ListCaseIterator
from openmdao.lib.caserecorders.api import DBCaseRecorder, DumpCaseRecorder, case_db_to_dict 
from openmdao.lib.drivers.simplecid import SimpleCaseIterDriver
from openmdao.main.uncertain_distributions import NormalDistribution

from openmdao.main.caseiter import caseiter_to_dict
    
class DBCaseRecorderTestCase(unittest.TestCase):

    def setUp(self):
        self.top = top = set_as_top(Assembly())
        driver = top.add('driver', SimpleCaseIterDriver())
        top.add('comp1', ExecComp(exprs=['z=x+y']))
        top.add('comp2', ExecComp(exprs=['z=x+1']))
        top.connect('comp1.z', 'comp2.x')
        driver.workflow.add(['comp1', 'comp2'])
        
        # now create some Cases
        outputs = [('comp1.z', None, None), ('comp2.z', None, None)]
        cases = []
        for i in range(10):
            inputs = [('comp1.x', None, i), ('comp1.y', None, i*2)]
            cases.append(Case(inputs=inputs, outputs=outputs, ident='case%s'%i))
        driver.iterator = ListCaseIterator(cases)

    def test_inoutDB(self):
        """This test runs some cases, puts them in a DB using a DBCaseRecorder,
        then runs the model again using the same cases, pulled out of the DB
        by a DBCaseIterator.  Finally the cases are dumped to a string after
        being run for the second time.
        """
        self.top.driver.recorder = DBCaseRecorder()
        self.top.run()
        
        # now use the DB as source of Cases
        self.top.driver.iterator = self.top.driver.recorder.get_iterator()
        
        sout = StringIO.StringIO()
        self.top.driver.recorder = DumpCaseRecorder(sout)
        self.top.run()
        expected = [
            'Case: case8',
            '   inputs:',
            '      comp1.x = 8',
            '      comp1.y = 16',
            '   outputs:',
            '      comp1.z = 24.0',
            '      comp2.z = 25.0',
            '   max_retries: None, retries: 1',
            ]
        self.assertTrue('\n'.join(expected) in sout.getvalue())
    
    def test_pickle_conversion(self):
        recorder = DBCaseRecorder()
        for i in range(10):
            inputs = [('comp1.x', None, i), ('comp1.y', None, i*2.)]
            outputs = [('comp1.z', None, i*1.5), ('comp2.normal', None, NormalDistribution(float(i),0.5))]
            recorder.record(Case(inputs=inputs, outputs=outputs, ident='case%s'%i))
        iterator = recorder.get_iterator()
        for i,case in enumerate(iterator.get_iter()):
            self.assertTrue(isinstance(case.outputs[1][2], NormalDistribution))
            self.assertEqual(case.outputs[1][2].mu, float(i))
            self.assertEqual(case.outputs[1][2].sigma, 0.5)
            self.assertTrue(isinstance(case.inputs[1][2], float))
            self.assertEqual(case.inputs[1][2], i*2.)
            self.assertEqual(case.outputs[0][2], i*1.5)
            
    def test_query(self):
        recorder = DBCaseRecorder()
        for i in range(10):
            inputs = [('comp1.x', None, i), ('comp1.y', None, i*2.)]
            outputs = [('comp1.z', None, i*1.5), ('comp2.normal', None, NormalDistribution(float(i),0.5))]
            recorder.record(Case(inputs=inputs, outputs=outputs, ident='case%s'%i))
        iterator = recorder.get_iterator()
        iterator.selectors = ["value>=0","value<3"]

        count = 0
        for i,case in enumerate(iterator.get_iter()):
            count += 1
            for name,idx,value in case.inputs:
                self.assertTrue(value >= 0 and value<3)
            for name,idx,value in case.outputs:
                self.assertTrue(value >= 0 and value<3)
        self.assertEqual(count, 3)

    def test_tables_already_exist(self):
        dbdir = tempfile.mkdtemp()
        dbname = os.path.join(dbdir,'junk_dbfile')
        
        recorder = DBCaseRecorder(dbname)
        recorder._connection.close()
        recorder = DBCaseRecorder(dbname, append=True)
        recorder._connection.close()
        try:
            recorder = DBCaseRecorder(dbname)
            recorder._connection.close()
        except Exception as err:
            self.assertEqual('table cases already exists', str(err))
        else:
            self.fail('expected Exception')
        try:
            shutil.rmtree(dbdir)
        except OSError:
            logging.error("problem removing directory %s" % dbdir)
        
    def test_db_to_dict(self):
        tmpdir = tempfile.mkdtemp()
        dfile = os.path.join(tmpdir, 'junk.db')
        recorder = DBCaseRecorder(dfile)
        
        # create some Cases where some are missing a variable
        outputs = [('comp1.z', None, None), ('comp2.z', None, None)]
        cases = []
        for i in range(10):
            if i>1:
                msg = ''
            else:
                msg = 'an error occurred'
            if i<5:
                inputs = [('comp1.x', None, i), ('comp1.y', None, i*2), ('comp1.y2', None, i*3)]
            else:
                inputs = [('comp1.x', None, i), ('comp1.y', None, i*2)]
            recorder.record(Case(inputs=inputs, outputs=outputs, ident='case%s'%i, msg=msg))

        varnames = ['comp1.x','comp1.y','comp1.y2']
        varinfo = case_db_to_dict(dfile, varnames)
        
        self.assertEqual(len(varinfo), 3)
        # each var list should have 3 data values in it (5 with the required variables minus
        # 2 with errors
        for name,lst in varinfo.items():
            self.assertEqual(len(lst), 3)
            
        # now use caseiter_to_dict to grab the same data
        varinfo = caseiter_to_dict(recorder.get_iterator(), varnames)
        # each var list should have 3 data values in it (5 with the required variables minus
        # 2 with errors
        for name,lst in varinfo.items():
            self.assertEqual(len(lst), 3)
        
        try:
            shutil.rmtree(tmpdir)
        except OSError:
            logging.error("problem removing directory %s" % tmpdir)

if __name__ == '__main__':
    unittest.main()
