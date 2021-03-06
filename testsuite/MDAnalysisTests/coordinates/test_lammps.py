# -*- Mode: python; tab-width: 4; indent-tabs-mode:nil; coding:utf-8 -*-
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
#
# MDAnalysis --- http://www.mdanalysis.org
# Copyright (c) 2006-2017 The MDAnalysis Development Team and contributors
# (see the file AUTHORS for the full list of names)
#
# Released under the GNU Public Licence, v2 or any higher version
#
# Please cite your use of MDAnalysis in published work:
#
# R. J. Gowers, M. Linke, J. Barnoud, T. J. E. Reddy, M. N. Melo, S. L. Seyler,
# D. L. Dotson, J. Domanski, S. Buchoux, I. M. Kenney, and O. Beckstein.
# MDAnalysis: A Python package for the rapid analysis of molecular dynamics
# simulations. In S. Benthall and S. Rostrup editors, Proceedings of the 15th
# Python in Science Conference, pages 102-109, Austin, TX, 2016. SciPy.
#
# N. Michaud-Agrawal, E. J. Denning, T. B. Woolf, and O. Beckstein.
# MDAnalysis: A Toolkit for the Analysis of Molecular Dynamics Simulations.
# J. Comput. Chem. 32 (2011), 2319--2327, doi:10.1002/jcc.21787
#
from __future__ import absolute_import
import os
import numpy as np
import pytest

import MDAnalysis as mda
from MDAnalysis import NoDataError

from numpy.testing import (assert_equal, assert_almost_equal, assert_raises,
                           assert_, assert_array_almost_equal)

from MDAnalysisTests import tempdir, make_Universe
from MDAnalysisTests.coordinates.reference import (
    RefLAMMPSData, RefLAMMPSDataMini, RefLAMMPSDataDCD,
)
from MDAnalysisTests.datafiles import (
    LAMMPScnt, LAMMPShyd, LAMMPSdata, LAMMPSdata_mini
)

from unittest import TestCase

def test_datareader_ValueError():
    from MDAnalysis.coordinates.LAMMPS import DATAReader
    assert_raises(ValueError, DATAReader, 'filename')


class _TestLammpsData_Coords(TestCase):
    """Tests using a .data file for loading single frame.

    All topology loading from MDAnalysisTests.data is done in test_topology
    """

    __test__ = False

    def setUp(self):
        self.u = mda.Universe(self.filename)

    def tearDown(self):
        del self.u

    def test_n_atoms(self):
        assert_equal(self.u.atoms.n_atoms, self.n_atoms)

    def test_coords(self):
        assert_equal(self.u.atoms[0].position, self.pos_atom1)

    def test_velos(self):
        assert_almost_equal(self.u.atoms[0].velocity, self.vel_atom1)

    def test_dimensions(self):
        assert_equal(self.u.dimensions, self.dimensions)

    def test_singleframe(self):
        assert_raises(StopIteration, self.u.trajectory.next)

    def test_seek(self):
        assert_raises(IndexError, self.u.trajectory.__getitem__, 1)

    def test_seek_2(self):
        ts = self.u.trajectory[0]
        assert_equal(type(ts), mda.coordinates.base.Timestep)

    def test_iter(self):
        # Check that iterating works, but only gives a single frame
        assert_equal(len(list(iter(self.u.trajectory))), 1)


class TestLammpsData_Coords(_TestLammpsData_Coords, RefLAMMPSData):
    __test__ = True


class TestLammpsDataMini_Coords(_TestLammpsData_Coords, RefLAMMPSDataMini):
    __test__ = True


@pytest.fixture(params = [
    LAMMPSdata,
    LAMMPSdata_mini,
    LAMMPScnt,
    LAMMPShyd,
], scope='module')
def LAMMPSDATAWriter(request, tmpdir_factory):
    filename = request.param
    u = mda.Universe(filename)
    fn = os.path.split(filename)[1]
    outfile = str(tmpdir_factory.mktemp('data').join(fn))

    with mda.Writer(outfile, n_atoms=u.atoms.n_atoms) as w:
        w.write(u.atoms)

    u_new = mda.Universe(outfile)

    return u, u_new


class TestLAMMPSDATAWriter(object):
    def test_Writer_dimensions(self, LAMMPSDATAWriter):
        u_ref, u_new = LAMMPSDATAWriter
        assert_almost_equal(u_ref.dimensions, u_new.dimensions,
                         err_msg="attributes different after writing",
                         decimal=6)

    @pytest.mark.parametrize('attr', [
        'types', 'bonds', 'angles', 'dihedrals', 'impropers'
    ])
    def test_Writer_atoms(self, attr, LAMMPSDATAWriter):
        u_ref, u_new = LAMMPSDATAWriter
        if hasattr(u_ref.atoms, attr):
            assert_equal(getattr(u_ref.atoms, attr),
                         getattr(u_new.atoms, attr),
                         err_msg="attributes different after writing")
        else:
            with pytest.raises(AttributeError):
                getattr(u_new, attr)

    @pytest.mark.parametrize('attr', [
        'masses', 'charges', 'velocities', 'positions'
    ])
    def test_Writer_numerical_attrs(self, attr, LAMMPSDATAWriter):
        u_ref, u_new = LAMMPSDATAWriter
        try:
            refvals = getattr(u_ref, attr)
        except (AttributeError):
            with pytest.raises(AttributeError):
                getattr(u_new, attr)
        else:
            assert_almost_equal(refvals,
                                getattr(u_new.atoms,attr),
                                err_msg="attributes different after writing",
                                decimal=6)


class TestLAMMPSDATAWriter_data_partial(TestLAMMPSDATAWriter):
    N_kept = 5

    @staticmethod
    @pytest.fixture()
    def LAMMPSDATA_partial(tmpdir):
        filename = LAMMPSdata
        N_kept = 5
        u = mda.Universe(filename)
        ext = os.path.splitext(filename)[1]
        outfile = str(tmpdir.join('lammps-data-writer-test' + ext))

        with mda.Writer(outfile, n_atoms=N_kept) as w:
            w.write(u.atoms[:N_kept])

        u_new = mda.Universe(outfile)

        return u, u_new

    @pytest.mark.parametrize('attr', [
        'masses', 'charges', 'velocities', 'positions'
    ])
    def test_Writer_atoms(self, attr, LAMMPSDATA_partial):
        u_ref, u_new = LAMMPSDATA_partial
        if hasattr(u_ref.atoms, attr):
            assert_almost_equal(getattr(u_ref.atoms[:self.N_kept], attr),
                                getattr(u_new.atoms, attr),
                                err_msg="attributes different after writing",
                                decimal=6)
        else:
            with pytest.raises(AttributeError):
                getattr(u_new, attr)

    def test_n_bonds(self, LAMMPSDATA_partial):
        u_ref, u_new = LAMMPSDATA_partial
        assert_equal(len(u_new.atoms.bonds), 4)

    def test_n_angles(self, LAMMPSDATA_partial):
        u_ref, u_new = LAMMPSDATA_partial
        assert_equal(len(u_new.atoms.angles), 4)


# need more tests of the LAMMPS DCDReader

class TestLAMMPSDCDReader(TestCase, RefLAMMPSDataDCD):
    flavor = 'LAMMPS'

    def setUp(self):
        self.u = mda.Universe(self.topology, self.trajectory,
                              format=self.format)

    def tearDown(self):
        del self.u

    def test_Reader_is_LAMMPS(self):
        assert_(self.u.trajectory.flavor, self.flavor)

    def get_frame_from_end(self, offset):
        iframe = self.u.trajectory.n_frames - 1 - offset
        iframe = iframe if iframe > 0 else 0
        return iframe

    def test_n_atoms(self):
        assert_equal(self.u.atoms.n_atoms, self.n_atoms)

    def test_n_frames(self):
        assert_equal(self.u.trajectory.n_frames, self.n_frames)

    def test_dimensions(self):
        mean_dimensions = np.mean([ts.dimensions for ts in self.u.trajectory],
                                  axis=0)
        assert_almost_equal(mean_dimensions, self.mean_dimensions)

    def test_dt(self):
        assert_almost_equal(self.u.trajectory.dt, self.dt,
                            err_msg="Time between frames dt is wrong.")

    def test_Timestep_time(self):
        iframe = self.get_frame_from_end(1)
        assert_almost_equal(self.u.trajectory[iframe].time,
                            iframe * self.dt,
                            err_msg="Time for frame {0} (dt={1}) is wrong.".format(
                iframe, self.dt))

    def test_LAMMPSDCDReader_set_dt(self, dt=1500.):
        u = mda.Universe(self.topology, self.trajectory, format=self.format,
                         dt=dt)
        iframe = self.get_frame_from_end(1)
        assert_almost_equal(u.trajectory[iframe].time, iframe*dt,
                            err_msg="setting time step dt={0} failed: "
                            "actually used dt={1}".format(
                dt, u.trajectory._ts_kwargs['dt']))

    def test_wrong_time_unit(self):
        def wrong_load(unit="nm"):
            return mda.Universe(self.topology, self.trajectory, format=self.format,
                                timeunit=unit)
        assert_raises(TypeError, wrong_load)

    def test_wrong_unit(self):
        def wrong_load(unit="GARBAGE"):
            return mda.Universe(self.topology, self.trajectory, format=self.format,
                                timeunit=unit)
        assert_raises(ValueError, wrong_load)


class TestLAMMPSDCDWriter(TestCase, RefLAMMPSDataDCD):
    flavor = 'LAMMPS'

    def setUp(self):
        self.u = mda.Universe(self.topology, self.trajectory,
                              format=self.format)
        # dummy output file
        ext = os.path.splitext(self.trajectory)[1]
        self.tmpdir = tempdir.TempDir()
        self.outfile = os.path.join(self.tmpdir.name,  'lammps-writer-test' + ext)

    def tearDown(self):
        try:
            os.unlink(self.outfile)
        except OSError:
            pass
        del self.u
        del self.tmpdir

    def test_Writer_is_LAMMPS(self):
        with mda.Writer(self.outfile, n_atoms=self.u.atoms.n_atoms,
                       format=self.format) as W:
            assert_(W.flavor, self.flavor)

    def test_Writer(self, n_frames=3):
        W = mda.Writer(self.outfile, n_atoms=self.u.atoms.n_atoms,
                       format=self.format)
        with self.u.trajectory.OtherWriter(self.outfile) as w:
            for ts in self.u.trajectory[:n_frames]:
                w.write(ts)
        short = mda.Universe(self.topology, self.outfile)
        assert_equal(short.trajectory.n_frames, n_frames,
                     err_msg="number of frames mismatch")
        assert_almost_equal(short.trajectory[n_frames - 1].positions,
                            self.u.trajectory[n_frames - 1].positions,
                            6, err_msg="coordinate mismatch between corresponding frames")

    def test_OtherWriter_is_LAMMPS(self):
        with self.u.trajectory.OtherWriter(self.outfile) as W:
            assert_(W.flavor, self.flavor)

    def test_OtherWriter(self):
        times = []
        with self.u.trajectory.OtherWriter(self.outfile) as w:
            for ts in self.u.trajectory[::-1]:
                times.append(ts.time)
                w.write(ts)
        # note: the reversed trajectory records times in increasing
        #       steps, and NOT reversed, i.e. the time markers are not
        #       attached to their frames. This could be considered a bug
        #       but DCD has no way to store timestamps. Right now, we'll simply
        #       test that this is the case and pass.
        reversed = mda.Universe(self.topology, self.outfile)
        assert_equal(reversed.trajectory.n_frames, self.u.trajectory.n_frames,
                     err_msg="number of frames mismatch")
        rev_times = [ts.time for ts in reversed.trajectory]
        assert_almost_equal(rev_times, times[::-1], 6,
                            err_msg="time steps of written DCD mismatch")
        assert_almost_equal(reversed.trajectory[-1].positions,
                            self.u.trajectory[0].positions,
                            6, err_msg="coordinate mismatch between corresponding frames")

class TestLAMMPSDCDWriterClass(TestCase):
    flavor = 'LAMMPS'

    def setUp(self):
        # dummy output file
        ext = ".dcd"
        self.tmpdir = tempdir.TempDir()
        self.outfile = os.path.join(self.tmpdir.name,  'lammps-writer-test' + ext)

    def tearDown(self):
        try:
            os.unlink(self.outfile)
        except OSError:
            pass
        del self.tmpdir

    def test_Writer_is_LAMMPS(self):
        with mda.coordinates.LAMMPS.DCDWriter(self.outfile, n_atoms=10) as W:
            assert_(W.flavor, self.flavor)

    def test_open(self):
        try:
            with mda.coordinates.LAMMPS.DCDWriter(self.outfile, n_atoms=10):
                pass
        except Exception:
            pytest.fail()

    def test_wrong_time_unit(self):
        with pytest.raises(TypeError):
            with mda.coordinates.LAMMPS.DCDWriter(self.outfile, n_atoms=10,
                                                  timeunit='nm'):
                pass

    def test_wrong_unit(self):
        with pytest.raises(ValueError):
            with mda.coordinates.LAMMPS.DCDWriter(self.outfile, n_atoms=10,
                                                  timeunit='GARBAGE'):
                pass


def test_triclinicness():
    u = mda.Universe(LAMMPScnt)

    assert u.dimensions[3] == 90.
    assert u.dimensions[4] == 90.
    assert u.dimensions[5] == 120.


@pytest.fixture
def tmpout(tmpdir):
    return str(tmpdir.join('out.data'))

class TestDataWriterErrors(object):
    def test_write_no_masses(self, tmpout):
        u = make_Universe(('types',), trajectory=True)

        try:
            u.atoms.write(tmpout)
        except NoDataError as e:
            assert_('masses' in e.args[0])
        else:
            pytest.fail()

    def test_write_no_types(self, tmpout):
        u = make_Universe(('masses',), trajectory=True)

        try:
            u.atoms.write(tmpout)
        except NoDataError as e:
            assert_('types' in e.args[0])
        else:
            pytest.fail()

    def test_write_non_numerical_types(self, tmpout):
        u = make_Universe(('types', 'masses'), trajectory=True)

        try:
            u.atoms.write(tmpout)
        except ValueError as e:
            assert_('must be convertible to integers' in e.args[0])
        else:
            raise pytest.fail()
