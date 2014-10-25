import pyaudio
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import sys
import time

FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
BYTE_DURATION = 0.1
CHUNK = 1024
CHUNKS_PER_BYTE = int((RATE*BYTE_DURATION) / CHUNK)

def tone(i):
  return (float(RATE) / CHUNK) * i

SYNC_TONE = 140
SYNC_FQ = tone(SYNC_TONE)
TONES = [ 60 + 10*x for x in range(0, 8) ]
FREQUENCIES = [tone(x) for x in TONES]

NOISE_THRESHOLD = 5
NOISE_CUTOFF = 0.1
PEAK_BAND = 30

GRAPH = False

print "sample rate: {0} Hz".format(RATE)
print "chunk size: {0}".format(CHUNK)
print "chunk / byte: {0}".format(CHUNKS_PER_BYTE)
print "carrier fq's: {0}".format(FREQUENCIES)
print "sync fq: {0}".format(SYNC_FQ)

pa = pyaudio.PyAudio()
stream = pa.open(format=FORMAT,
  channels=CHANNELS,
  rate=RATE,
  input=True,
  frames_per_buffer=CHUNK)

if GRAPH:
  min_fq = min([ SYNC_FQ, min(FREQUENCIES) ]) - 100
  max_fq = max([ SYNC_FQ, max(FREQUENCIES) ]) + 100
  min_tone = min([ SYNC_TONE, min(TONES) ]) - 5
  max_tone = max([ SYNC_TONE, max(TONES) ]) + 5
  plt.ion()
  fig = plt.figure()
  ax1 = fig.add_subplot(311)
  spectrum_graph = ax1.plot([])[0]
  peaks_graph = ax1.plot([], 'ro')[0]
  ax1.set_ylim([0, 200])
  ax1.set_xlim([min_fq, max_fq])
  for fq in FREQUENCIES:
    ax1.axvline(fq, 0, 100, color='gray')
  ax1.axvline(SYNC_FQ, 0, 100, color='r')
  ax1.axhline(NOISE_THRESHOLD, 0, max_fq, color='gray')

  ax2 = fig.add_subplot(312)
  ax2.set_ylim([-1.1 * np.pi, 1.1 * np.pi])
  ax2.set_xlim([0, 100])
  sync_phase_history_graph = ax2.plot([], 'g.-')[0]

  ax3 = fig.add_subplot(313)
  ax3.set_ylim([-1.1* np.pi, 1.1 * np.pi])
  ax3.set_xlim([min_tone, max_tone])
  phase_graph = ax3.plot([], 'g.-')[0]

  plt.draw()
  plt.show()

window = signal.gaussian(3, 10, False)
byte_buffer = []
sync_phase_history = []
phase_history = []
byte_phase_history = []
chunk_no = 0
last_sync = 0

def frequency_to_fft_idx(fq):
  return int((float(fq) / (RATE / 2)) * (CHUNK / 2))

while True:
  try:
    block = stream.read(CHUNK)
    decoded = np.fromstring(block, 'Float32');

    fft = np.fft.rfft(decoded)
    spectrum = np.abs(fft)
    spectrum = signal.resample(spectrum, RATE/2)
    phase_spectrum = np.angle(fft)

    peak_threshold = max(max(spectrum) * NOISE_CUTOFF, NOISE_THRESHOLD)
    peakidx = filter(lambda idx: spectrum[idx] > peak_threshold, signal.argrelmax(spectrum)[0])
    peakval = [ spectrum[idx] for idx in peakidx ]

    phaseidx = TONES + [ SYNC_TONE ]
    phaseval = [ phase_spectrum[idx] for idx in phaseidx ]
    syncval = phase_spectrum[SYNC_TONE]
    sync_phase_history.append(syncval)
    sync_phase_history = sync_phase_history[-100:]
    phase_history.append(phaseval[:-1])

    if np.std(sync_phase_history[-CHUNKS_PER_BYTE:]) < np.pi / 8:
      if last_sync + CHUNKS_PER_BYTE <= chunk_no:
        last_sync = chunk_no

        bph = np.average(phase_history[-CHUNKS_PER_BYTE:], axis=0)
        byte_phase_history.append(bph)

        if len(byte_phase_history) > 1:
          bits = [ 1 if abs(byte_phase_history[-1][bitno] - byte_phase_history[-2][bitno]) > 0.5*np.pi else 0 for bitno in range(0, 8) ]
          byte = np.sum([ 2 ** idx if bit else 0 for idx, bit in enumerate(bits) ])
          char = chr(byte) if 32 <= byte <=126 else '.'
          sys.stdout.write(char)
          sys.stdout.flush()
          byte_buffer.append(byte)

    chunk_no +=1

    if GRAPH:
      spectrum_graph.set_data(range(0, len(spectrum)), spectrum)
      peaks_graph.set_data(peakidx, peakval)
      sync_phase_history_graph.set_data(range(0, len(sync_phase_history)), sync_phase_history)
      phase_graph.set_data(phaseidx, phaseval)
      plt.draw()
  except IOError:
    continue
