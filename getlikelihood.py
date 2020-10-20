from matplotlib import pyplot
import h5py
import numpy
import logging
import pycbc
from pycbc import conversions
from pycbc.detector import Detector
from pycbc.inference import models
from pycbc.workflow import WorkflowConfigParser
from pycbc.inference import io

pycbc.init_logging(True)
direct = 'emcee_pt/baseline_13'
#rundir = '/work/stephanie.brown/phdwork/cosmic_explorer/emcee_pt/baseline_13/baseline_emceept_relative_13_output/local-site-scratch/work/baseline_emceept_relative_13-main_ID0000001/baseline_emceept_relative_13-bns_ID0000001'
#fp = io.loadfile('{}/H1L1-INFERENCE_BNS-1187008492-108.hdf.checkpoint'.format(rundir), 'r')

#direct = 'emcee_pt/baseline_10'
rundir = '/work/stephanie.brown/phdwork/cosmic_explorer/emcee_pt/baseline_10/baseline_emceept_relative_10_output/local-site-scratch/work/baseline_emceept_relative_10-main_ID0000001/baseline_emceept_relative_10-bns_ID0000001'
fp = io.loadfile('{}/H1L1-INFERENCE_BNS-1187008492-108.hdf.checkpoint'.format(rundir), 'r')

ifp = h5py.File('{}/injection.hdf'.format(direct), 'r')

samples = fp.read_samples(list(fp['samples'].keys()))
sortidx = samples['loglikelihood'].argsort()
injection = ifp.attrs['distance'], ifp.attrs['inclination']
print(injection)

xarg = 'distance'
xlabel = r'$d_{L}$ (Mpc)'
yarg = 'inclination'
ylabel = r'$\iota$'

fig, ax = pyplot.subplots(dpi=200)
sc = ax.scatter(samples[xarg][sortidx], samples[yarg][sortidx],
                c=samples['snr_from_loglr(loglikelihood-lognl)'][sortidx])
fig.colorbar(sc)
ax.set_xlabel(xlabel)
ax.set_ylabel(ylabel)
ax.grid()
pyplot.savefig('/work/stephanie.brown/WWW/cosmic_explorer/singleplots/var_distance/dis_inc_loglikelihood_marg_phase.png')
pyplot.clf()


regionarg = 'distance'

vals = samples[regionarg]
logls = samples['loglikelihood']
maxl_indices = []

lwrbnd = 33
upperbnd = 300

print("lower bound = ", lwrbnd, "\ upper bound = ", upperbnd)

mask = (vals >= lwrbnd) & (vals < upperbnd)
logli = logls[mask]
maxl_indices.append((mask, logli.argmax()))


xarg = 'distance'
xlabel = r'$d_{L}$ (Mpc)'
yarg = 'inclination'
ylabel = r'$\iota$'


fig, ax = pyplot.subplots(dpi=200)
sc = ax.scatter(samples[xarg][sortidx], samples[yarg][sortidx],
                c=samples['snr_from_loglr(loglikelihood-lognl)'][sortidx])
# plot used point in each region
for ii, (mask, idx) in enumerate(maxl_indices):
    # plot the used point
    ax.scatter(samples[xarg][mask][idx], samples[yarg][mask][idx], color='k', marker='x')
    # plot a line for the upper bound
ax.axhline(injection[1], ls='-', color='r')
ax.axvline(injection[0], ls='-', color='r')
#ax.axhline(-0.42, ls='-', color='b')
#ax.axvline(3.452, ls='-', color='b')
fig.colorbar(sc)
ax.set_xlabel(xlabel)
ax.set_ylabel(ylabel)
ax.grid()

pyplot.savefig('/work/stephanie.brown/WWW/cosmic_explorer/singleplots/var_distance/dis_inc_max_loglikelihood_marg_phase.png')
pyplot.clf()


cp = WorkflowConfigParser(
	'{r}/data_baseline.ini {r}/sampler.ini {r}/bns_inference.ini {r}/marginalized_phase.ini'
	 .format(r=direct).split()
	)
	       

"""cp = WorkflowConfigParser(
	'{r}/data_baseline.ini {r}/sampler.ini {r}/bns_marginalized_phase.ini '
	 .format(r=direct).split()
	)"""



"""cp = WorkflowConfigParser(
	'{r}/data_baseline.ini {r}/sampler.ini {r}/bns_relative.ini '
	 .format(r=direct).split()
	)"""

model = models.read_from_config(cp)

data = {}
whdata = {}
for det in model.data:
    d = model.data[det]
    data[det] = d.to_timeseries()
    d = d.copy()
    d *= model.weight[det] / (4*model.psds[det].delta_f)**0.5
    whdata[det] = d.to_timeseries()


waveforms = []
whitened_waveforms = []
snrs = []
for mask, maxidx in maxl_indices:
    print(maxidx)
    # generate the waveforms using the model
    params = {p: samples[p][mask][maxidx] for p in model.sampling_params}
    print('mass1 > mass2:', params['srcmass1'] > params['srcmass2'])
    #params['mode_array'] = [(2,2)]

    print('mass1 > mass2:', params['srcmass1'] > params['srcmass2'])
    if params['srcmass2'] > params['srcmass1']:
        p2 = params.copy()
        for p in ['srcmass{}', 'spin{}z']:
            p2[p.format(1)] = params[p.format(2)]
            p2[p.format(2)] = params[p.format(1)]
        params = p2
    print('now, mass1 > mass2:', params['srcmass1'] > params['srcmass2'])
    model.update(**params)
    model.loglikelihood
    print("current stat keys = ", model.current_stats.keys())
    #pol = model.current_stats['maxl_polarization']
    #phi = model.current_stats['maxl_phase']
    # store the maxl snr
    maxloglr = model.current_stats['loglr']
    snr = conversions.snr_from_loglr(maxloglr)
    print("snr at current params = ", snr)
    snrs.append(snr)
    print("max loglr = ", maxloglr, " \t snr = ", snr)
    """wfs = model.model.waveform_generator.generate(
        polarization=pol, coa_phase=phi,
        **model.current_params)"""
    print("current params = ", model.current_params)
    wfs = model.model.waveform_generator.generate(
        **model.current_params)
    hs = {}
    whitend_hs = {}
    for detname in wfs:
        det = Detector(detname)
        fp, fc = det.antenna_pattern(model.current_params['ra'],
                                     model.current_params['dec'],
                                     pol,
                                     model.current_params['tc'])
        hp, hc = wfs[detname]
        h = fp*hp + fc*hc
        h.resize(len(model.weight[detname]))
        flow = model.current_params['f_lower']
        hs[detname] = pycbc.waveform.fd_to_td(h, left_window=(flow, flow+5))
        wh = h.copy()
        wh *= model.weight[detname] / (4*model.psds[detname].delta_f)**0.5
        whitend_hs[detname] = wh.to_timeseries()
    waveforms.append(hs)
    whitened_waveforms.append(whitend_hs)

print(model.model.waveform_generator.current_params)

