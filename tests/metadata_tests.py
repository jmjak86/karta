import unittest
import numpy as np
from karta.vector.metadata import Metadata

class TestMetadata(unittest.TestCase):

    def setUp(self):
        self.onefield = Metadata(data=np.arange(200))
        self.multifield = Metadata(data={"a":np.arange(200),
                                         "b":np.arange(200,400), 
                                         "c":np.arange(200)**2})
        return

    def test_indexing(self):
        self.assertEqual(self.onefield[10], (10,))
        self.assertEqual(set(self.multifield[10]), set([10, 210, 100]))
        return

    def test_get(self):
        self.assertEqual(self.onefield.get(10), {"value": 10})
        self.assertEqual(self.multifield.get(10), {"a":10, "b": 210, "c": 100})
        return

    def test_slicing(self):
        self.assertTrue(np.all(self.onefield.get(slice(5,15))["value"] == np.arange(5, 15)))
        res = self.multifield.get(slice(5,15))
        self.assertTrue(np.all(res["a"] == np.arange(5, 15)))
        self.assertTrue(np.all(res["b"] == np.arange(205, 215)))
        self.assertTrue(np.all(res["c"] == np.arange(5, 15)**2))
        return

    def test_keys(self):
        self.assertTrue(np.all(self.onefield.getfield("value") == np.arange(200)))
        self.assertTrue(np.all(self.multifield.getfield("a") == np.arange(200)))
        self.assertTrue(np.all(self.multifield.getfield("b") == np.arange(200, 400)))
        self.assertTrue(np.all(self.multifield.getfield("c") == np.arange(200)**2))
        return

    def test_reference_vs_value_list(self):
        # metadata objects should carry values rather than references
        L = [1,2,3,4,5]
        md = Metadata(L)
        L[3] = -99
        self.assertEqual(md.getfield("value"), [1,2,3,4,5])
        return

    def test_reference_vs_value_dict(self):
        # metadata objects should carry values rather than references
        D = {"A":[1,2,3,4,5],
             "B":[6,7,8,9,10]}
        md = Metadata(D)
        D["A"][3] = -99
        self.assertEqual(md.getfield("A"), [1,2,3,4,5])
        return

    def test_nan_values(self):
        D = {"A":[1,np.nan,3,4,5],
             "B":[6,7,8,np.nan,10]}
        md = Metadata(D)
        self.assertTrue(np.isnan(md.getfield("A")[1]))
        self.assertEqual(md.getfield("A"), md.getfield("A"))
        return

    def test_none_values(self):
        D = {"A":[1,None,3,4,5],
             "B":[6,7,8,None,10]}
        md = Metadata(D)
        self.assertTrue(md.getfield("A")[1] is None)
        self.assertEqual(md.getfield("A"), md.getfield("A"))
        return

    def test_init_specified_fields(self):
        md = Metadata([(1,2,3),(4,5,6),(7,8,9)], fields=("a","b","c"))
        self.assertEqual(md.data, [(1,2,3),(4,5,6),(7,8,9)])
        self.assertEqual(md.fields, ("a","b","c"))
        return

    def test_init_specified_fields2(self):
        md = Metadata([("by air",),("by land,"),("by sea",)], fields=("mode",))
        self.assertEqual(md.data, [("by air",),("by land,"),("by sea",)])
        self.assertEqual(md.fields, ("mode",))
        return

    def test_extend(self):
        md1 = Metadata({"street": ["F. R. Lillie", "School St.", "Quissett Ave."],
                        "number": [3784, 78, 83]})
        md2 = Metadata({"street": ["Winding Ln.", "Oyster Pond Rd."],
                        "color": ["Grey", "White"]})
        md1.extend(md2)
        self.assertEqual(len(md1), 5)
        self.assertEqual(set((None, "Winding Ln.")), set(md1[3]))
        return

    def test_addfield(self):
        # data, field syntax used in order to specify field order
        md = Metadata([("F R. Lillie", 3784), ("School St.", 78), ("Quissett Ave.", 83)],
                      fields=("street", "number"))
        md.setfield("driveway", [True, True, False])
        ans = Metadata([("F R. Lillie", 3784, True), ("School St.", 78, True),
                        ("Quissett Ave.", 83, False)],
                       fields=("street", "number", "driveway"))
        self.assertEqual(md, ans)
        return

    def test_updatefield(self):
        md = Metadata({"street": ["F. R. Lillie", "School St.", "Quissett Ave."],
                       "number": [3784, 78, 83]})
        md.setfield("number", [3782, 78, 83])
        ans = Metadata({"street": ["F. R. Lillie", "School St.", "Quissett Ave."],
                        "number": [3782, 78, 83]})
        self.assertEqual(md, ans)
        return

if __name__ == "__main__":
    unittest.main()

