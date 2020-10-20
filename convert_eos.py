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

"""# get other physical information
eos_dat_columns = ['eos', 'radius_1p4', 'max_mass', 'cs_sq_max', 'cs_sq_1p9',
                   'pmax', 'p1p9', 'p2nsat', 'p4nsat', 'radius_1p6',
                   'threshold_mass']
#dt = [(p, str if p == 'eos' else float) for p in eos_dat_columns]
dt = [(p, float) for p in eos_dat_columns]
eos_data = numpy.loadtxt(opts.eos_dat_file, dtype=dt)
eos_params = eos_dat_columns[1:]
print("eos daa shape = ", np.shape(eos_data))
# make sure eos index is increasing
eos_data.sort(order='eos')"""

eos_params = 'eos' 
eos = numpy.genfromtxt(opts.eos_dat_file, dtype=str)
for f in eos:
    f = f.replace('/work/cdcapano/projects/eft_eos/eft-eos/New_M_Lam_files_2nsat/','')
    f = f.replace('.dat','')
    f = float(f)


fp = loadfile(opts.posterior_file, 'a')
samples = fp.read_samples(['srcmass1', 'srcmass2', 'eos'])

numpy.random.seed(opts.seed)
print( 'applying transforms')
tsamps = {}
for ii in range(samples.size):
    s = samples[ii]
    print("transforms = ", ts)
    m = transforms.apply_transforms({p: s[p] for p in samples.fieldnames}, ts)
    # also add the radius  
    for t in ts:
        mass = s[t.mass_param]
        eos = t.get_eos(int(s['eos']))
        radii = eos.lambda_from_tov_data(mass, t.distance, eos.data['mass'],
                                         eos.data['radius'])
        m['radius{}'.format(t.mass_param[-1])] = radii
    for p in m:
        try:
            tsamps[p][ii] = m[p]
        except KeyError:
            tsamps[p] = numpy.zeros(samples.size)
            tsamps[p][ii] = m[p]
    # add additional eos info
    # convert eos number to index
    eosidx = int(s['eos']) - 1
    for p in eos_params:
        try:
            tsamps[p][ii] = eos_data[eosidx][p]
        except KeyError:
            tsamps[p] = numpy.zeros(samples.size)
            tsamps[p][ii] = eos_data[eosidx][p]
    # add some noise for mthresh to account for systematics
    #tsamps['threshold_mass'][ii] += numpy.random.normal(scale=0.05)

print( 'writing')
# write
for p in ['lambda1', 'lambda2', 'radius1', 'radius2']+eos_params:
    fp['samples'][p] = tsamps[p]
# convert the masses to source masses
#fp['samples']['mass1'][:] = samples['mass1/(1+redshift(distance))']
#fp['samples']['mass2'][:] = samples['mass2/(1+redshift(distance))']

fp.close()
