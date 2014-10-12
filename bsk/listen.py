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

FREQUENCY = 430.6640625
SIMULATION = False

print "sample rate: {0} Hz".format(RATE)
print "chunk size: {0}".format(CHUNK)
print "fq: {0}".format(FREQUENCY)

pa = pyaudio.PyAudio()
stream = pa.open(format=FORMAT,
  channels=CHANNELS,
  rate=RATE,
  input=True,
  frames_per_buffer=CHUNK)

plt.ion()
min_fq = 0
max_fq = CHUNK / 2
fig = plt.figure()

ax1 = fig.add_subplot(311)
spectrum_graph = ax1.plot([])[0]
ax1.set_ylim([0, 200])
ax1.set_xlim([min_fq, max_fq])

ax2 = fig.add_subplot(312)
phase_graph = ax2.plot([], 'g-')[0]
ax2.set_ylim([-1.1*np.pi, 1.1*np.pi])
ax2.set_xlim([0, 20])

ax3 = fig.add_subplot(313)
phase_history_graph = ax3.plot([], 'g-')[0]
ax3.set_ylim([-1.1*np.pi, 1.1*np.pi])
ax3.set_xlim([0, 100])

plt.draw()
plt.show()

if SIMULATION:
  oscillators = [ [ np.sin((2 * i * np.pi / RATE) * FREQUENCY) for i in range(0, 10*RATE) ],
                  [ np.sin((2 * i * np.pi / RATE) * FREQUENCY + np.pi) for i in range(0, 10*RATE) ] ]

i = 0
phase_history = []

while True:
  try:
    if SIMULATION:
      byte_no = int(i*CHUNK/BYTE_DURATION / RATE)
      decoded = oscillators[byte_no%2][i*CHUNK:(i+1)*CHUNK]
      i+=1
    else:
      block = stream.read(CHUNK)
      decoded = np.fromstring(block, 'Float32');

    fft = np.fft.rfft(decoded)
    spectrum = np.abs(fft)
    phase_spectrum = np.angle(fft)
    peak = np.argmax(spectrum)
    phase = phase_spectrum[peak]
    print peak, phase_spectrum[peak:peak+2], phase
    phase_history.append(phase)
    phase_history = phase_history[-100:]

    spectrum_graph.set_data(range(0, len(spectrum)), spectrum)
    phase_graph.set_data(range(0, len(phase_spectrum)), phase_spectrum)
    phase_history_graph.set_data(range(0, len(phase_history)), phase_history)

    plt.draw()
  except IOError:
    continue
