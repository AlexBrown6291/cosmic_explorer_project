import numpy as np
import pycbc
from pycbc import waveform
from pycbc import filter
from pycbc.psd import aLIGOZeroDetHighPower
#from pycbc import fake_strain_from_file

f_low = 10.
sample_rate = 2048
seg_length = 8
delta_f = 1.0/seg_length


#for l in [3.2, 6.7, 22.6]:
# Generate the two waveforms to compare
hp, hc = waveform.get_fd_waveform(approximant="IMRPhenomD_NRTidal",
                         mass1=1.4,
                         mass2=1.4,
                         lambda1=740,
                         lambda2=740,
			 distance=100,
                         f_lower=f_low,
                         delta_t=1.0/sample_rate,
			 delta_f=1.0/seg_length)

# Resize the waveforms to the same length
tlen = len(hp)
#hp.resize(tlen)

# Generate the aLIGO ZDHP PSD
#delta_f = 1.0 / hp.duration
flen = tlen//2 + 1
psd_voyager = pycbc.psd.from_txt('/work/stephanie.brown/phdwork/cosmic_explorer/ce_curves/strain/ce1_30km_cb.txt',flen,delta_f,f_low,is_asd_file=True)
#psd = aLIGOZeroDetHighPower(flen, delta_f, f_low)
#print(len(psd))
#hp.resize(len(psd))
hp.resize(len(psd_voyager))

print( (flen+1)*delta_f/2 + f_low)

# Note: This takes a while the first time as an FFT plan is generated
# subsequent calls are much faster.
snr = filter.sigma(hp, psd=psd_voyager, low_frequency_cutoff=f_low)
print('The snr is: {:.0f}'.format(snr))
