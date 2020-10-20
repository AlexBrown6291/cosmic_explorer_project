#! /usr/bin/env python
import numpy
from pycbc import transforms
from pycbc.inference.io import loadfile
from pycbc.workflow import WorkflowConfigParser
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--config-file', nargs='+', required=True)
parser.add_argument('--posterior-file', required=True)
parser.add_argument('--eos-dat-file', required=True)
parser.add_argument('--seed', type=int, help='Set seed for mthresh noise.')

opts = parser.parse_args()

cp = WorkflowConfigParser(opts.config_file)
ts = transforms.read_transforms_from_config(cp, section='waveform_transforms')

eos_params = 'eos' 
eos = numpy.genfromtxt(opts.eos_dat_file, dtype=str)
for f in eos:
    f = f.replace('/work/cdcapano/projects/eft_eos/eft-eos/New_M_Lam_files_2nsat/','')
    f = f.replace('.dat','')
    f = float(f)

fp = loadfile(opts.posterior_file, 'a')
samples = fp.read_samples(['srcmass1', 'srcmass2', 'eos'])


