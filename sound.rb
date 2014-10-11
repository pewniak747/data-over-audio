require 'coreaudio'

payload = if ARGV[0] then ARGV[0] else "Hello World" end.encode("ascii")
bytes = payload.unpack("C*")

def tone(i)
  (2 ** (i.to_f / 12)) * 440
end

SYNC_FQ = tone(38).to_i
FREQUENCIES = Array.new(8) { |i| tone(30 + i).to_i }

puts "payload:\t#{payload}"
puts "bytes:\t\t#{bytes}"
puts "fqs:\t\t#{FREQUENCIES}"
puts "sync fq:\t#{SYNC_FQ}"

dev = CoreAudio.default_output_device
byte_duration = 0.05
sync_duration = byte_duration / 4
SAMPLE_RATE = dev.nominal_rate
BUFFER_SIZE = (byte_duration * SAMPLE_RATE).to_i
SYNC_SIZE = (sync_duration * SAMPLE_RATE).to_i
BUFFER = dev.output_buffer(BUFFER_SIZE)

BUFFER.start

def play_text(text)
  play_bytes(text.unpack('C*'))
end

def play_bytes(bytes)
  sync_signal = Array.new(SYNC_SIZE) { |i| Math.sin((2 * i * Math::PI / SAMPLE_RATE) * SYNC_FQ) }
  wave = NArray.sint(BUFFER_SIZE)

  bytes.each do |byte|

    mods = 8.times.map do |i|
      0 != (byte & 0b01 << i)
    end

    samples = BUFFER_SIZE.times.map do |i|
      sines = FREQUENCIES.zip(mods).map do |f, m|
        sine = Math.sin((2 * i * Math::PI / SAMPLE_RATE) * f)
        if m
          sine
        else
          0.0
        end
      end
      sines << sync_signal[i] if i < sync_signal.size
      sines.reduce(:+) / (FREQUENCIES.size + 1)
    end
    samples.map.with_index do |sample, i|
      wave[i] = sample * 32767
    end
    BUFFER << wave
  end
end

while text = $stdin.read(16) do
  play_text(text)
end

sleep byte_duration

BUFFER.stop
