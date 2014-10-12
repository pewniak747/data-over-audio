import pyaudio
import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt
import sys
import time

FORMAT = pyaudio.paFloat32
CHANNELS = 1
RATE = 44100
BYTE_DURATION = 0.075
CHUNKS_PER_BYTE = 3
CHUNK = int(RATE * BYTE_DURATION / CHUNKS_PER_BYTE)

def tone(i):
  return (2 ** (i / 12)) * 440

SYNC_FQ = int(tone(38.0))
FREQUENCIES = [int(tone(30.0 + x)) for x in range(0, 8)]
NOISE_THRESHOLD = 5
NOISE_CUTOFF = 0.3
PEAK_BAND = 30
GRAPH = False

def detect_peak(fq, peaks):
  return any(filter(lambda peak: fq - PEAK_BAND <= peak <= fq + PEAK_BAND, peaks))

print "sample rate: {0} Hz".format(RATE)
print "chunk size: {0}".format(CHUNK)
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
  plt.ion()
  spectrum_graph = plt.plot([])[0]
  peaks_graph = plt.plot([], 'ro')[0]
  phase_graph = plt.plot([], 'go')[0]
  plt.ylim([0, 100])
  plt.xlim([min_fq, max_fq])
  for fq in FREQUENCIES:
    plt.axvline(fq, 0, 100, color='gray')
  plt.axvline(SYNC_FQ, 0, 100, color='r')
  plt.axhline(NOISE_THRESHOLD, 0, max_fq, color='gray')
  plt.draw()
  plt.show()

window = signal.gaussian(3, 10, False)
byte_buffer = []

while True:
  try:
    block = stream.read(CHUNK)
    decoded = np.fromstring(block, 'Float32');

    fft = np.fft.rfft(decoded)
    fft = signal.resample(fft, RATE/2)
    spectrum = np.abs(fft)
    phase_spectrum = np.angle(fft)

    peak_threshold = max(max(spectrum) * NOISE_CUTOFF, NOISE_THRESHOLD)
    peakidx = filter(lambda idx: spectrum[idx] > peak_threshold, signal.argrelmax(spectrum)[0])
    peakval = [ spectrum[idx] for idx in peakidx ]

    phaseidx = FREQUENCIES + [ SYNC_FQ ]
    phaseval = [ phase_spectrum[fq] for fq in phaseidx ]

    sync = detect_peak(SYNC_FQ, peakidx)
    bts = map(lambda x: 1 if detect_peak(x, peakidx) else 0, FREQUENCIES)
    byte = np.sum([ 2 ** idx if bit else 0 for idx, bit in enumerate(bts) ])
    #char = chr(byte) if 32 <= byte <=126 else '.'
    #print "{0}\t{1}\t{2}".format(byte, char, sync)
    if sync:
      if len(byte_buffer) >= CHUNKS_PER_BYTE:
        bts = byte_buffer[-CHUNKS_PER_BYTE:]
        byte_buffer = []
        counts = np.bincount(bts)
        winner = np.argmax(counts)
        char = chr(winner) if 32 <= winner <=126 else '.'
        sys.stdout.write(char)
        sys.stdout.flush()
    byte_buffer.append(byte)

    if GRAPH:
      spectrum_graph.set_data(range(0, len(spectrum)), spectrum)
      peaks_graph.set_data(peakidx, peakval)
      phase_graph.set_data(phaseidx, phaseval)
      plt.draw()
  except IOError:
    continue
