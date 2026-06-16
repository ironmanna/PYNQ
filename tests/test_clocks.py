# Copyright (C) 2022 Xilinx, Inc
# SPDX-License-Identifier: BSD-3-Clause

import math
import pynq
import pytest
import importlib
import os
import numpy as np
from .mock_devices import MockMemoryMappedDevice


ZU_LPD_OFFSET = 0xFF5E0000
ZU_FPD_OFFSET = 0xFD1A0000


class FakeUname:
    def __init__(self, machine):
        self.machine = machine


def be_zu():
    return FakeUname(pynq.ps.ZU_ARCH)


def be_other():
    return FakeUname('Invalid Arch')


ZU_READ_PLLS = {
    'iopll': (1, 0x20, 0x0050300),
    'rpll': (1, 0x30, 0x0050302),
    'dpll': (0, 0x2C, 0x0050303),
}

ZU_READ_CLKS = {
    'fclk0_mhz': 0xc0,
    'fclk1_mhz': 0xc4,
    'fclk2_mhz': 0xc8,
    'fclk3_mhz': 0xcC,
}

ZU_CPU_PLLS = {
    'apll': (0x20, 0x200),
    'dpll': (0x2C, 0x202),
    'vpll': (0x38, 0x203),
}


@pytest.fixture
def setup_zu(monkeypatch):
    old_arch = pynq.ps.CPU_ARCH
    monkeypatch.setattr(os, 'uname', be_zu)
    device = MockMemoryMappedDevice('zu_clocks')
    pynq.Device.active_device = device
    lpd_buffer = device.mmap(ZU_LPD_OFFSET, 0x100)
    lpd_array = np.frombuffer(lpd_buffer, dtype='u4')

    fpd_buffer = device.mmap(ZU_FPD_OFFSET, 0x100)
    fpd_array = np.frombuffer(fpd_buffer, dtype='u4')

    new_ps = importlib.reload(pynq.ps)
    Clocks = new_ps.Clocks
    Clocks.device = device
    Clocks.device.arch = os.uname().machine

    yield Clocks, lpd_array, fpd_array

    pynq.Device.active_device = None
    pynq.ps.CPU_ARCH = old_arch


def split_zu_reg(reg_val):
    source = (reg_val) & 0x07
    div0 = (reg_val >> 8) & 0x3F
    div1 = (reg_val >> 16) & 0x3F
    return source, div0, div1


@pytest.mark.parametrize('pll_name', ZU_READ_PLLS.keys())
@pytest.mark.parametrize('clk_name', ZU_READ_CLKS.keys())
def test_zu_pl(setup_zu, pll_name, clk_name):
    pll_region, pll_reg, clk_val = ZU_READ_PLLS[pll_name]
    clk_reg = ZU_READ_CLKS[clk_name]
    Clocks, lpd_array, fpd_array = setup_zu

    if pll_region:
        lpd_array[pll_reg >> 2] = 45 << 8  # FBDIV of 45 (1500 MHz)
    else:
        fpd_array[pll_reg >> 2] = 45 << 8

    lpd_array[clk_reg >> 2] = clk_val

    assert math.isclose(getattr(Clocks, clk_name), 99.999)

    if pll_name == 'iopll':
        setattr(Clocks, clk_name, 50)
        source, div0, div1 = split_zu_reg(lpd_array[clk_reg >> 2])
        assert div0 * div1 == 30
        assert source == 0


@pytest.mark.parametrize('pll_name', ZU_READ_PLLS.keys())
@pytest.mark.parametrize('clk_name', ZU_READ_CLKS.keys())
def test_zu_pl_div2(setup_zu, pll_name, clk_name):
    pll_region, pll_reg, clk_val = ZU_READ_PLLS[pll_name]
    clk_reg = ZU_READ_CLKS[clk_name]
    Clocks, lpd_array, fpd_array = setup_zu

    if pll_region:
        lpd_array[pll_reg >> 2] = 0x10000 | (45 << 8)  # FBDIV of 45 (1500 MHz)
    else:
        fpd_array[pll_reg >> 2] = 0x10000 | (45 << 8)

    lpd_array[clk_reg >> 2] = clk_val

    assert math.isclose(getattr(Clocks, clk_name), 49.9995)

    if pll_name == 'iopll':
        setattr(Clocks, clk_name, 25)
        source, div0, div1 = split_zu_reg(lpd_array[clk_reg >> 2])
        assert div0 * div1 == 30
        assert source == 0


def test_invalid_clkidx(setup_zu):
    Clocks, lpd_array, fpd_array = setup_zu
    with pytest.raises(ValueError):
        Clocks.get_pl_clk(-1)
    with pytest.raises(ValueError):
        Clocks.get_pl_clk(4)
    with pytest.raises(ValueError):
        Clocks.set_pl_clk(-1)
    with pytest.raises(ValueError):
        Clocks.set_pl_clk(4)


@pytest.mark.parametrize('pll_name', ZU_READ_PLLS.keys())
def test_zu_invalid_source(setup_zu, pll_name):
    pll_region, pll_reg, clk_val = ZU_READ_PLLS[pll_name]
    clk_reg = ZU_READ_CLKS['fclk0_mhz']
    Clocks, lpd_array, fpd_array = setup_zu
    if pll_region:
        lpd_array[pll_reg >> 2] = 0x10000 | (45 << 8) | (4 << 20)
    else:
        fpd_array[pll_reg >> 2] = 0x10000 | (45 << 8) | (4 << 20)

    lpd_array[clk_reg >> 2] = clk_val
    with pytest.raises(ValueError):
        Clocks.fclk0_mhz


@pytest.mark.parametrize('pll_name', ZU_CPU_PLLS.keys())
def test_zu_cpu(setup_zu, pll_name):
    pll_reg, clk_val = ZU_CPU_PLLS[pll_name]
    Clocks, lpd_array, fpd_array = setup_zu

    fpd_array[pll_reg >> 2] = 45 << 8
    fpd_array[0x60 >> 2] = clk_val

    assert Clocks.cpu_mhz == 749.9925


def test_invalid_arch(monkeypatch):
    device = MockMemoryMappedDevice('invalid_arch')
    monkeypatch.setattr(os, 'uname', be_other)
    new_ps = importlib.reload(pynq.ps)
    Clocks = new_ps.Clocks
    Clocks.device = device
    Clocks.device.arch = os.uname().machine
    with pytest.raises(RuntimeError):
        Clocks.fclk0_mhz


def test_delayed_mmio(monkeypatch):
    old_arch = pynq.ps.CPU_ARCH
    try:
        monkeypatch.setattr(os, 'uname', be_zu)
        device = MockMemoryMappedDevice('zu_clocks')
        pynq.Device.active_device = device
        new_ps = importlib.reload(pynq.ps)
        Clocks = new_ps.Clocks

        assert len(device.regions) == 0
    finally:
        pynq.Device.active_device = None
        pynq.ps.CPU_ARCH = old_arch
