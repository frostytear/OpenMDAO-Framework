# pylint: disable-msg=C0111,C0103

import unittest

from enthought.traits.api import Float, Str, Instance
from openmdao.main.api import Assembly, Component

class Multiplier(Component):
    rval_in = Float(iostatus='in')
    rval_out = Float(iostatus='out')
    mult = Float(iostatus='in')
    
    def __init__(self, name):
        super(Multiplier, self).__init__(name)
        self.rval_in = 4.
        self.rval_out = 7.
        self.mult = 1.5
        self.run_count = 0

    def execute(self):
        self.run_count += 1
        self.rval_out = self.rval_in * self.mult
        
class Simple(Component):
    
    a = Float(iostatus='in')
    b = Float(iostatus='in')
    c = Float(iostatus='out')
    d = Float(iostatus='out')
    
    def __init__(self, name, parent=None):
        super(Simple, self).__init__(name, parent)
        self.a = 4.
        self.b = 5.
        self.c = 7.
        self.d = 1.5
        self.run_count = 0

    def execute(self):
        self.run_count += 1
        self.c = self.a + self.b
        self.d = self.a - self.b

class DummyComp(Component):
    
    r = Float(iostatus='in')
    r2 = Float(iostatus='in')
    s = Str(iostatus='in')
    rout = Float(iostatus='out')
    r2out = Float(iostatus='out')
    sout = Str(iostatus='out')
    
    dummy_in = Instance(Component, iostatus='in')
    dummy_out = Instance(Component, iostatus='out')
    
    def __init__(self, name, parent=None):
        super(DummyComp, self).__init__(name, parent)
        self.r = 1.0
        self.r2 = -1.0
        self.rout = 0.0
        self.r2out = 0.0
        self.s = 'a string'
        self.sout = ''
        
        # make a nested container with input and output ContainerVars
        self.add_child(Multiplier('dummy'))
        self.dummy_in = self.dummy
        self.dummy_out = self.dummy
                
    def execute(self):
        self.rout = self.r * 1.5
        self.r2out = self.r2 + 10.0
        self.sout = self.s[::-1]
        # pylint: disable-msg=E1101
        self.dummy.execute()


class AssemblyTestCase(unittest.TestCase):

    def setUp(self):
        """
        top
            comp1
            nested
                comp1
            comp2
            comp3
        """
        self.asm = Assembly('top', None)
        dc1 = DummyComp('comp1', self.asm)        
        nested = Assembly('nested', self.asm)
        nested_dc = DummyComp('comp1', nested)        
        children = [DummyComp(x, self.asm) for x in ['comp2','comp3']]
        
    def test_lazy_eval(self):
        top = Assembly('top', None)
        top.add_child(Multiplier('comp1'))
        top.add_child(Multiplier('comp2'))
        top.comp1.mult = 2.0
        top.comp2.mult = 4.0
        top.connect('comp1.rval_out', 'comp2.rval_in')
        top.set('comp1.rval_in', 5.0)
        top.run()
        self.assertEqual(top.get('comp1.rval_out'), 10.)
        self.assertEqual(top.get('comp2.rval_in'), 10.)
        self.assertEqual(top.get('comp2.rval_out'), 40.)
        self.assertEqual(top.comp1.run_count, 1)
        self.assertEqual(top.comp2.run_count, 1)
        
        # now change an input (mult) on comp2. This should only 
        # cause comp2 to execute when we run next time.
        top.set('comp2.mult', 3.0)
        top.run()
        self.assertEqual(top.get('comp1.rval_out'), 10.)
        self.assertEqual(top.get('comp2.rval_in'), 10.)
        self.assertEqual(top.get('comp2.rval_out'), 30.)
        self.assertEqual(top.comp1.run_count, 1)
        self.assertEqual(top.comp2.run_count, 2)
        
     
    def test_data_passing(self):
        comp1 = self.asm.get('comp1')
        comp2 = self.asm.get('comp2')
        self.asm.connect('comp1.rout','comp2.r')
        self.asm.connect('comp1.sout','comp2.s')
        self.asm.set('comp1.r', 3.0)
        self.asm.set('comp1.s', 'once upon a time')
        self.assertEqual(comp1.get('r'), 3.0)
        self.assertEqual(comp1.get('s'), 'once upon a time')
        self.assertEqual(comp1.r, 3.0)
        self.assertEqual(comp1.s, 'once upon a time')
        
        self.asm.run()
        
        self.assertEqual(comp1.get('rout'), 4.5)
        self.assertEqual(comp1.get('sout'), 'emit a nopu ecno')       
        self.assertEqual(comp1.rout, 4.5)
        self.assertEqual(comp1.sout, 'emit a nopu ecno')
        self.assertEqual(comp2.get('r'), 4.5)
        self.assertEqual(comp2.get('rout'), 6.75)
        self.assertEqual(comp2.r, 4.5)
        self.assertEqual(comp2.rout, 6.75)
        self.assertEqual(comp2.s, 'emit a nopu ecno')
        self.assertEqual(comp2.sout, 'once upon a time')

    def test_connect_containers(self):
        self.asm.set('comp1.dummy_in.rval_in', 75.4)
        self.asm.connect('comp1.dummy_out','comp2.dummy_in')
        self.asm.run()
        self.assertEqual(self.asm.get('comp2.dummy_in.rval_in'), 75.4)
        self.assertEqual(self.asm.get('comp2.dummy_in.rval_out'), 75.4*1.5)
    
    ## currently, connecting directly to/from Variables from a Container
    ## inside of a ContainerVariable is not allowed.  Maybe later we can
    ## add the ability to create passthru variables on-the-fly or something
    #def test_connect_containers_sub(self):
        #self.asm.set('comp1.dummy_in.rval_in', 75.4)
        #self.asm.connect('comp1.dummy_out.rval_out','comp2.dummy_in.rval_in')
        #self.asm.run()
        #self.assertEqual(self.asm.get('comp2.dummy_in.rval_in'), 75.4*1.5)
        
    def test_create_passthru(self):
        self.asm.set('comp3.r', 75.4)
        self.asm.create_passthru('comp3.rout')
        self.assertEqual(self.asm.get('comp3.r'), 75.4)
        self.assertEqual(self.asm.get('rout'), 0.0)
        self.asm.run()
        self.assertEqual(self.asm.get('comp3.rout'), 75.4*1.5)
        self.assertEqual(self.asm.get('rout'), 75.4*1.5)
        
    def test_passthru_nested(self):
        self.asm.set('comp1.r', 8.)
        self.asm.nested.create_passthru('comp1.r')
        self.asm.nested.create_passthru('comp1.rout', 'foobar')
        self.asm.connect('comp1.rout', 'nested.r')
        self.asm.connect('nested.foobar','comp2.r')
        self.asm.run()
        self.assertEqual(self.asm.get('comp1.rout'), 12.)
        self.assertEqual(self.asm.get('comp2.rout'), 27.)
                
    def test_create_passthru_alias(self):
        self.asm.nested.set('comp1.r', 75.4)
        self.asm.nested.create_passthru('comp1.r','foobar')
        self.assertEqual(self.asm.nested.get('foobar'), 75.4)
        self.asm.run()
        self.assertEqual(self.asm.nested.get('foobar'), 75.4)
        
    def test_passthru_already_connected(self):
        self.asm.connect('comp1.rout','comp2.r')
        self.asm.connect('comp1.sout','comp2.s')
        # this should fail since we're creating a second connection
        # to an input
        try:
            self.asm.create_passthru('comp2.r')
        except RuntimeError, err:
            self.assertEqual(str(err), 'top: comp2.r is already connected')
        else:
            self.fail('RuntimeError expected')
        self.asm.set('comp1.s', 'some new string')
        # this one should be OK since outputs can have multiple connections
        self.asm.create_passthru('comp1.sout')
        self.asm.run()
        self.assertEqual(self.asm.get('sout'), 'some new string'[::-1])
        
    def test_container_passthru(self):
        self.asm.set('comp1.dummy_out.rval_in', 75.4)
        self.asm.create_passthru('comp1.dummy_out','dummy_out_passthru')
        self.asm.run()
        self.assertEqual(self.asm.get('dummy_out_passthru.rval_out'), 75.4*1.5)

#    def test_discon_reconnect_passthru(self):
#        self.fail('unfinished test')
        
    def test_invalid_connect(self):
        try:
            self.asm.connect('comp1.rout','comp2.rout')
        except RuntimeError, err:
            self.assertEqual('top: top.comp2.rout must be an input variable',
                             str(err))
        else:
            self.fail('exception expected')
        try:
            self.asm.connect('comp1.r','comp2.rout')
        except RuntimeError, err:
            self.assertEqual('top: top.comp1.r must be an output variable',
                             str(err))
        else:
            self.fail('exception expected')
            
    def test_self_connect(self):
        try:
            self.asm.connect('comp1.rout','comp1.r')
        except RuntimeError, err:
            self.assertEqual('top: Cannot connect comp1.rout to comp1.r. Both are on same component.',
                             str(err))
        else:
            self.fail('exception expected')
     
    def test_attribute_link(self):
        try:
            self.asm.connect('comp1.rout.units','comp2.s')
        except NameError, err:
            self.assertEqual(str(err), 
                    "top: Cannot locate trait named 'rout.units'")
        else:
            self.fail('NameError expected')
        
    def test_value_link(self):
        try:
            self.asm.connect('comp1.rout.value','comp2.r2')
        except NameError, err:
            self.assertEqual(str(err), 
                    "top: Cannot locate trait named 'rout.value'")
        else:
            self.fail('NameError expected')
        
     
    def test_circular_dependency(self):
        self.asm.connect('comp1.rout','comp2.r')
        try:
            self.asm.connect('comp2.rout','comp1.r')
        except RuntimeError, err:
            self.assertEqual("top.dataflow: circular dependency (['comp2', 'comp1']) would be created by"+
                             " connecting comp2.rout to comp1.r", str(err))
        else:
            self.fail('exception expected')
            
    def test_disconnect(self):
        # first, run connected
        comp2 = self.asm.get('comp2')
        self.asm.connect('comp1.rout', 'comp2.r')
        self.asm.run()
        self.assertEqual(comp2.r, 1.5)
        self.asm.comp1.r = 3.0
        self.asm.run()
        self.assertEqual(comp2.r, 4.5)
        
        # now disconnect
        self.asm.comp1.r = 6.0
        self.asm.disconnect('comp2.r')
        self.asm.run()
        self.assertEqual(comp2.r, 4.5)
        
        # now reconnect
        self.asm.connect('comp1.rout','comp2.r')
        self.asm.run()
        self.assertEqual(comp2.r, 9.0)
        
    def test_input_passthru_to_2_inputs(self):
        asm = Assembly('top')
        nest = Assembly('nested', asm)
        Simple('comp1', nest)
        Simple('comp2', nest)
        nest.create_passthru('comp1.a') 
        nest.connect('a', 'comp2.b') 
        self.assertEqual(nest.comp1.a, 4.)
        self.assertEqual(nest.comp2.b, 5.)
        nest.a = 0.5
        self.assertEqual(nest.comp1.a, 0.5)
        self.assertEqual(nest.comp2.b, 5.)
        self.assertEqual(nest.comp2.get_valid('b'), False)
        asm.run()
        self.assertEqual(nest.comp1.a, 0.5)
        self.assertEqual(nest.comp2.b, 0.5)
        
    def test_connect_2_outs_to_passthru(self):
        asm = Assembly('top')
        nest = Assembly('nested', asm)
        Simple('comp1', nest)
        Simple('comp2', nest)
        nest.create_passthru('comp1.c')
        try:
            nest.connect('comp2.d', 'c')
        except RuntimeError, err:
            self.assertEqual(str(err), 'top.nested: c is already connected')
        else:
            self.fail('RuntimeError expected')
        
 
    def test_discon_not_connected(self):
        self.asm.connect('comp1.rout','comp2.r')
        
        # disconnecting something that isn't connected is ok and shouldn't
        # raise an exception
        self.asm.disconnect('comp2.s')

    def test_listcon_with_deleted_objs(self):
        self.asm.add_child(DummyComp('comp3'))
        self.asm.connect('comp1.rout', 'comp2.r')
        self.asm.connect('comp3.sout', 'comp2.s')
        conns = self.asm.list_connections()
        self.assertEqual(conns, [('comp1.rout', 'comp2.r'),
                                 ('comp3.sout', 'comp2.s')])
        self.asm.remove_child('comp3')
        conns = self.asm.list_connections()
        self.assertEqual(conns, [('comp1.rout', 'comp2.r')])
        self.asm.run()
        
        
if __name__ == "__main__":
    unittest.main()


