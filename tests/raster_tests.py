""" Unit tests for raster functions """

import unittest
import os
import numpy as np
from test_helper import TESTDATA

import karta
from karta.raster import _dem

class RegularGridTests(unittest.TestCase):

    def setUp(self):
        pe = karta.raster.peaks(n=49)
        self.rast = karta.RegularGrid((15.0, 15.0, 30.0, 30.0, 0.0, 0.0), values=pe)
        return

    def test_add_rgrid(self):
        rast2 = karta.RegularGrid(self.rast.transform,
                                  values=np.random.random(self.rast.values.shape)) 
        res = self.rast + rast2
        self.assertTrue(np.all(res.values == self.rast.values+rast2.values))
        return

    def test_sub_rgrid(self):
        rast2 = karta.RegularGrid(self.rast.transform,
                                  values=np.random.random(self.rast.values.shape)) 
        res = self.rast - rast2
        self.assertTrue(np.all(res.values == self.rast.values-rast2.values))
        return

    def test_center_coords(self):
        ans = np.meshgrid(np.arange(15.0, 1471.0, 30.0),
                          np.arange(15.0, 1471.0, 30.0))
        self.assertEqual(0.0, np.sum(self.rast.center_coords()[0] - ans[0]))
        self.assertEqual(0.0, np.sum(self.rast.center_coords()[1] - ans[1]))
        return

    def test_resample(self):
        # use linear function so that nearest neighbour and linear interp are
        # exact
        def makegrid(s, f, n):
            xx, yy = np.meshgrid(np.linspace(s, f, n),
                                 np.linspace(s, f, n))
            zz = 2.0*xx + -3.0*yy
            return karta.RegularGrid((15.0, 15.0, 30.0, 30.0, 0.0, 0.0), values=zz)

        g = makegrid(0.0, 1.0, 129)
        sol = makegrid(1.0/128.0, 1.0-1.0/128.0, 64)
        gnew = g.resample(60.0, 60.0)
        residue = gnew.values - sol.values
        self.assertTrue(np.max(np.abs(residue)) < 1e-12)
        return

    def test_sample_nearest(self):
        grid = karta.RegularGrid([0.5, 0.5, 1.0, 1.0, 0.0, 0.0],
                                 values=np.array([[0, 1], [1, 0.5]]))
        self.assertEqual(grid.sample_nearest(0.6, 0.7), 0.0)
        self.assertEqual(grid.sample_nearest(0.6, 1.3), 1.0)
        self.assertEqual(grid.sample_nearest(1.4, 0.3), 1.0)
        self.assertEqual(grid.sample_nearest(1.6, 1.3), 0.5)
        return

    def test_sample_bilinear(self):
        grid = karta.RegularGrid([0.5, 0.5, 1.0, 1.0, 0.0, 0.0],
                                 values=np.array([[0, 1], [1, 0.5]]))
        self.assertEqual(grid.sample_bilinear(1.0, 1.0), 0.625)
        return

    def test_sample_bilinear2(self):
        grid = karta.RegularGrid([0.5, 0.5, 1.0, 1.0, 0.0, 0.0],
                                 values=np.array([[0, 1], [1, 0.5]]))
        xi, yi = np.meshgrid(np.linspace(0.5, 1.5), np.linspace(0.5, 1.5))
        z = grid.sample_bilinear(xi.ravel(), yi.ravel())
        self.assertEqual([z[400], z[1200], z[1550], z[2120]],
                         [0.16326530612244894, 0.48979591836734693,
                          0.63265306122448983, 0.74052478134110788])
        return

    def test_vertex_coords(self):
        ans = np.meshgrid(np.arange(15.0, 1486.0, 30.0),
                          np.arange(15.0, 1486.0, 30.0))
        self.assertTrue(np.sum(self.rast.vertex_coords()[0] - ans[0]) < 1e-10)
        self.assertTrue(np.sum(self.rast.vertex_coords()[1] - ans[1]) < 1e-10)
        return

    def test_get_extents(self):
        creg = (15.0, 1455.0, 15.0, 1455.0)
        ereg = (0.0, 1470.0, 0.0, 1470.0)
        self.assertEqual(self.rast.get_extents(reference='center'), creg)
        self.assertEqual(self.rast.get_extents(reference='edge'), ereg)
        return

    def test_minmax(self):
        minmax = self.rast.minmax()
        self.assertEqual(minmax, (-6.5466445243204294, 8.075173545159231))
        return

    def test_clip(self):
        clipped = self.rast.clip(500, 900, 500, 900)
        self.assertEqual(clipped.size, (15, 15))
        self.assertEqual(clipped.transform, (495, 495, 30, 30, 0, 0))
        X, Y = clipped.center_coords()
        self.assertEqual(X[0,0], 495)
        self.assertEqual(X[0,-1], 915)
        self.assertEqual(Y[0,0], 495)
        self.assertEqual(Y[-1,0], 915)
        return

    def test_clip_to_extents(self):
        proto = karta.RegularGrid((495, 495, 30, 30, 0, 0), np.zeros((15,15)))
        clipped = self.rast.clip(*proto.get_extents())
        self.assertEqual(clipped.size, (15, 15))
        self.assertEqual(clipped.transform, (495, 495, 30, 30, 0, 0))
        X, Y = clipped.center_coords()
        self.assertEqual(X[0,0], 495)
        self.assertEqual(X[0,-1], 915)
        self.assertEqual(Y[0,0], 495)
        self.assertEqual(Y[-1,0], 915)

    def test_get_indices(self):
        ind = self.rast.get_indices(15.0, 15.0)
        self.assertEqual(tuple(ind), (0, 0))
        ind = self.rast.get_indices(1455.0, 1455.0)
        self.assertEqual(tuple(ind), (48, 48))
        return

    def test_get_indices_vec(self):
        ind = self.rast.get_indices(np.arange(15.0, 1470, 5),
                                    np.arange(15.0, 1470, 5))

        xi = np.array([ 0,  0,  0,  0,  1,  1,  1,  1,  1,  2,  2,  2,  2, 2,
            2, 2,  3, 3,  3,  3,  3,  4,  4,  4,  4,  4,  4,  4,  5,  5, 5,  5,
            5,  6, 6,  6,  6,  6,  6,  6,  7,  7,  7,  7,  7,  8,  8, 8,  8, 8,
            8, 8,  9,  9,  9,  9,  9, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11,
            11, 11, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 14, 14, 14,
            14, 14, 14, 14, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16, 16, 17,
            17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 20,
            20, 20, 20, 20, 20, 20, 21, 21, 21, 21, 21, 22, 22, 22, 22, 22, 22,
            22, 23, 23, 23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 25, 25, 25, 25,
            25, 26, 26, 26, 26, 26, 26, 26, 27, 27, 27, 27, 27, 28, 28, 28, 28,
            28, 28, 28, 29, 29, 29, 29, 29, 30, 30, 30, 30, 30, 30, 30, 31, 31,
            31, 31, 31, 32, 32, 32, 32, 32, 32, 32, 33, 33, 33, 33, 33, 34, 34,
            34, 34, 34, 34, 34, 35, 35, 35, 35, 35, 36, 36, 36, 36, 36, 36, 36,
            37, 37, 37, 37, 37, 38, 38, 38, 38, 38, 38, 38, 39, 39, 39, 39, 39,
            40, 40, 40, 40, 40, 40, 40, 41, 41, 41, 41, 41, 42, 42, 42, 42, 42,
            42, 42, 43, 43, 43, 43, 43, 44, 44, 44, 44, 44, 44, 44, 45, 45, 45,
            45, 45, 46, 46, 46, 46, 46, 46, 46, 47, 47, 47, 47, 47, 48, 48, 48,
            48, 48, 48])
        
        
        yi = np.array([ 0,  0,  0,  0,  1,  1,  1,  1,  1,  2,  2,  2,  2,  2,
            2, 2,  3, 3,  3,  3,  3,  4,  4,  4,  4,  4,  4,  4,  5,  5,  5,
            5, 5,  6, 6,  6,  6,  6,  6,  6,  7,  7,  7,  7,  7,  8,  8,  8,
            8, 8,  8, 8,  9,  9,  9,  9,  9, 10, 10, 10, 10, 10, 10, 10, 11,
            11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12, 13, 13, 13, 13, 13, 14,
            14, 14, 14, 14, 14, 14, 15, 15, 15, 15, 15, 16, 16, 16, 16, 16, 16,
            16, 17, 17, 17, 17, 17, 18, 18, 18, 18, 18, 18, 18, 19, 19, 19, 19,
            19, 20, 20, 20, 20, 20, 20, 20, 21, 21, 21, 21, 21, 22, 22, 22, 22,
            22, 22, 22, 23, 23, 23, 23, 23, 24, 24, 24, 24, 24, 24, 24, 25, 25,
            25, 25, 25, 26, 26, 26, 26, 26, 26, 26, 27, 27, 27, 27, 27, 28, 28,
            28, 28, 28, 28, 28, 29, 29, 29, 29, 29, 30, 30, 30, 30, 30, 30, 30,
            31, 31, 31, 31, 31, 32, 32, 32, 32, 32, 32, 32, 33, 33, 33, 33, 33,
            34, 34, 34, 34, 34, 34, 34, 35, 35, 35, 35, 35, 36, 36, 36, 36, 36,
            36, 36, 37, 37, 37, 37, 37, 38, 38, 38, 38, 38, 38, 38, 39, 39, 39,
            39, 39, 40, 40, 40, 40, 40, 40, 40, 41, 41, 41, 41, 41, 42, 42, 42,
            42, 42, 42, 42, 43, 43, 43, 43, 43, 44, 44, 44, 44, 44, 44, 44, 45,
            45, 45, 45, 45, 46, 46, 46, 46, 46, 46, 46, 47, 47, 47, 47, 47, 48,
            48, 48, 48, 48, 48])

        self.assertTrue(np.all(ind[0] == xi))
        self.assertTrue(np.all(ind[1] == yi))
        return

    def test_profile(self):
        path = karta.Line([(15.0, 15.0), (1484.0, 1484.0)], crs=karta.crs.Cartesian)
        _, z = self.rast.profile(path, resolution=42.426406871192853, method="nearest")
        expected = self.rast.values.diagonal()
        self.assertTrue(np.allclose(z, expected))
        return

    def test_read_aai(self):
        grid = karta.read_aai(os.path.join(TESTDATA,'peaks49.asc'))
        self.assertTrue(np.all(grid.values[::-1] == self.rast.values))
        return


class TestWarpedGrid(unittest.TestCase):

    def setUp(self):
        ii = np.arange(50.0)
        jj = np.arange(50.0)
        X, Y = np.meshgrid(np.sin(ii/25.0 * 2*np.pi),
                           np.sin(jj/50.0 * 2*np.pi))
        values = karta.raster.witch_of_agnesi(50, 50)
        self.rast = karta.WarpedGrid(X=X, Y=Y, values=values)

    def test_add_sgrid(self):
        rast2 = karta.WarpedGrid(X=self.rast.X, Y=self.rast.Y,
                                      values=np.random.random(self.rast.values.shape))
        res = self.rast + rast2
        self.assertTrue(np.all(res.values == self.rast.values+rast2.values))
        return

    def test_sub_sgrid(self):
        rast2 = karta.WarpedGrid(X=self.rast.X, Y=self.rast.Y,
                                 values=np.random.random(self.rast.values.shape))
        res = self.rast - rast2
        self.assertTrue(np.all(res.values == self.rast.values-rast2.values))
        return

class TestAAIGrid(unittest.TestCase):

    def setUp(self):
        pe = karta.raster.peaks(n=49)
        self.rast = karta.aaigrid.AAIGrid(pe, hdr={'ncols':49, 'nrows':49,
                                                   'xllcorner':0.0,
                                                   'yllcorner':0.0,
                                                   'cellsize':30.0,
                                                   'nodata_value':-9999})
        return

    def test_region_centered(self):
        reg = self.rast.get_region()
        self.assertEqual(reg, (15.0, 1485.0, 15.0, 1485.0))
        return

    def test_minmax(self):
        minmax = self.rast.minmax()
        self.assertEqual(minmax, (-6.5466445243204294, 8.075173545159231))
        return

    def test_get_indices(self):
        ind = self.rast.get_indices(0.0, 0.0)
        self.assertEqual(ind, (0, 48))
        ind = self.rast.get_indices(1485.0, 1485.0)
        self.assertEqual(ind, (48, 0))
        return

    def test_resize(self):
        orig = self.rast.data.copy()
        x0, x1, y0, y1 = self.rast.get_region()
        self.rast.resize((x0, x1/2.0, y0, y1/2.0))
        self.assertTrue(np.all(self.rast.data == orig[:25,:25]))
        return

class TestDEMDriver(unittest.TestCase):

    def setUp(self):
        pass

    def test_nreps_re(self):
        nr = _dem.nreps_re("2(I4,I2,F7.4)")
        self.assertEqual(nr, 2)
        nr = _dem.nreps_re("2(3I6)")
        self.assertEqual(nr, 6)
        nr = _dem.nreps_re("4(6F3.7)")
        self.assertEqual(nr, 24)
        return

    def test_parse(self):
        p = _dem.parse("2(I4,I2,F7.4)", ' -81 0 0.0000  82 0 0.0000')
        self.assertEqual(p, [-81, 0, 0.0, 82, 0, 0.0])
        return

    def test_dtype(self):
        t = _dem.dtype("2(I4,D24.15,F7.4)")
        self.assertEqual(t, [int, _dem.coerce_float, _dem.coerce_float])
        return

    def test_reclen(self):
        n = _dem.reclen("2(I4,I2,F7.4)")
        self.assertEqual(n, [4, 2, 7])
        return

#class TestInterpolation(unittest.TestCase):
#
#    def test_idw(self):
#        # Test inverse weighted distance interpolation
#        Xm, Ym = np.meshgrid(np.arange(10), np.arange(10))
#        G = np.c_[Xm.flat, Ym.flat]
#        obs = np.array(((2,4,5),(6,3,4),(3,9,9)))
#        D = raster.interpolation.interp_idw(G, obs, wfunc=lambda d: 1.0/(d+1e-16)**0.5)
#        self.assertEqual(D, np.array([ 5.77099225,  5.73080888,  5.68934588,
#                            5.64656361,  5.60263926, 5.56391335,  5.54543646,
#                            5.55810434,  5.59468599,  5.64001991, 5.7666018 ,
#                            5.71712039,  5.66733266,  5.61528705,  5.55254697,
#                            5.48200769,  5.44194711,  5.4718629 ,  5.54176929,
#                            5.61255561, 5.76627041,  5.70140932,  5.64212525,
#                            5.59011147,  5.50963694, 5.36912109,  5.24490032,
#                            5.34965772,  5.49388958,  5.59812945, 5.7765376 ,
#                            5.67823283,  5.58875282,  5.57796102,  5.51352082,
#                            5.30130025,  4.00000002,  5.2696964 ,  5.49251053,
#                            5.61373077, 5.81944097,  5.68356449,  5.00000001,
#                            5.61034065,  5.60629104, 5.47740263,  5.34297441,
#                            5.43952794,  5.57499849,  5.6693856 , 5.91915228,
#                            5.83714501,  5.76171956,  5.78893204,  5.78328667,
#                            5.71759216,  5.65687878,  5.66124481,  5.70678887,
#                            5.75517987, 6.06116315,  6.0515271 ,  6.04980015,
#                            6.05331942,  6.02324779, 5.95580534,  5.88858853,
#                            5.8514621 ,  5.84418368,  5.85242989, 6.21638838,
#                            6.27774217,  6.35281161,  6.38711869,  6.31999906,
#                            6.19926611,  6.09004119,  6.01415787,  5.96971255,
#                            5.94708184, 6.35785785,  6.4954344 ,  6.70982294,
#                            6.88076712,  6.68090612, 6.43193841,  6.26024319,
#                            6.14772366,  6.07568133,  6.03068086, 6.45468497,
#                            6.63857194,  6.9936249 ,  8.99999996,  6.97005635,
#                            6.58706897,  6.37686191,  6.24425398,  6.15677403,
#                            6.09829941]))
#        return

if __name__ == "__main__":
    unittest.main()

