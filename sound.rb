require 'coreaudio'

class Frame
  attr_reader :payload
  def initialize(payload)
    @payload = Array(payload)
    raise "invalid payload length: #{payload.length}. expected #{self.class.payload_length}" unless payload.length == self.class.payload_length
  end

  #  2 bytes - preamble
  # 16 bytes - payload
  #  6 bytes - error correction
  # 24 bytes - total
  def bytes
    # preamble + payload + error_correction
    payload
  end

  def self.payload_length
    16
  end

  def self.length
    16
  end

  private

  def preamble
    [0b01000010, 0b00100100]
  end

  def error_correction
    [1, 1, 1, 1, 1, 1] # TODO
  end
end

class Encoder
  def encode_text(text)
    encode(text.unpack('C*'))
  end

  def encode(bytes)
    bytes.each_slice(frame_payload_size).map { |payload|
      payload = payload + Array.new(frame_payload_size - payload.size) { 0b00 }
      Frame.new(payload)
    }
  end

  private

  def frame_payload_size
    Frame.payload_length
  end
end

class Player
  attr_reader :device, :sample_rate
  def initialize(device)
    @device = device
    @sample_rate = device.nominal_rate
  end

  def play(stream)
    puts "fqs:\t\t#{carrier_frequencies}"
    puts "sync fq:\t#{sync_frequency}"
    buffer = device.output_buffer(byte_buffer_size)
    wave = NArray.sint(byte_buffer_size)

    buffer.start

    stream.each_with_index do |frame, frame_idx|
      frame.bytes.each_with_index do |byte, byte_idx|

        mods = 8.times.map do |i|
          0 != (byte & 0b01 << i)
        end

        samples = byte_buffer_size.times.map do |i|
          sample_no = frame_idx*Frame.length*byte_buffer_size + byte_idx*byte_buffer_size + i
          sines = carrier_frequencies.zip(mods).map do |f, m|
            if m
              sine(sample_no, f)
            else
              0.0
            end
          end
          shift = if byte_idx % 2 == 0 then 0 else Math::PI end
          sines << sine(sample_no, sync_frequency, shift)
          sines.reduce(:+) / (carrier_frequencies.size + 1)
        end
        samples.map.with_index do |sample, i|
          wave[i] = sample * 32767
        end
        buffer << wave

      end
    end

    sleep byte_duration
    buffer.stop
  end

  private

  def sine(sample, frequency, phase_shift = 0)
    Math.sin((2 * sample * Math::PI / sample_rate) * frequency + phase_shift)
  end

  def byte_duration
    0.2
  end

  def byte_buffer_size
    (byte_duration * sample_rate).to_i
  end

  def sync_frequency
    @sfq ||= tone(140)
  end

  def carrier_frequencies
    @cfq ||= Array.new(8) { |i| tone(60 + 10*i) }
  end

  def tone(i)
    (sample_rate.to_f / 1024) * i
  end
end

device = CoreAudio.default_output_device
encoder = Encoder.new
player = Player.new(device)

while text = $stdin.read and text.length > 0 do
  frames = encoder.encode_text(text)
  player.play(frames)
end
