require 'coreaudio'

class Player
  attr_reader :device, :sample_rate
  def initialize(device)
    @device = device
    @sample_rate = device.nominal_rate
  end

  def play
    puts "fq:\t#{frequency}"
    buffer = device.output_buffer(buffer_size)
    wave = NArray.sint(buffer_size)

    buffer.start
    idx = 0

    loop do
      buffer_size.times do |i|
        sample_no = idx*buffer_size + i
        shift = if idx % 2 == 0 then 0 else Math::PI end
        wave[i] = sine(sample_no, frequency, shift) * 32767
      end

      buffer << wave
      idx += 1
    end

    buffer.stop
  end

  private

  def sine(sample, frequency, phase_shift = 0)
    Math.sin((2 * sample * Math::PI / sample_rate) * frequency + phase_shift)
  end

  def byte_duration
    1.0
  end

  def buffer_size
    (byte_duration * sample_rate).to_i
  end

  def frequency
    430.6640625
  end
end

device = CoreAudio.default_output_device
player = Player.new(device)
player.play()
