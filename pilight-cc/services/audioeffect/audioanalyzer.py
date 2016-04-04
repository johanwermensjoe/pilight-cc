import numpy
import pyaudio
import threading


class AudioRecorder:
    """ Simple, cross-platform class to record system audio. """

    RATE = 48100
    BUFFER_SIZE = 2 ** 12  # 1024 is a good buffer size

    def __init__(self):
        """ Constructor
        """
        self.sec_to_record = .1
        self.__shutdown = False
        self.new_audio = False

        # Initialize sound card.
        # TODO - windows detection vs. alsa or something for linux
        # TODO - try/except for sound card selection/initiation

        self.buffers_to_record = int(
            self.RATE * self.sec_to_record / self.BUFFER_SIZE)
        if self.buffers_to_record == 0:
            self.buffers_to_record = 1

        self.samples_to_record = int(self.BUFFER_SIZE * self.buffers_to_record)
        self.chunks_to_record = int(self.samples_to_record / self.BUFFER_SIZE)
        self.sec_per_point = 1.0 / self.RATE

        self.p = pyaudio.PyAudio()
        self.xs_buffer = numpy.arange(self.BUFFER_SIZE) * self.sec_per_point
        self.xs = numpy.arange(
            self.chunks_to_record * self.BUFFER_SIZE) * self.sec_per_point
        self.audio = numpy.empty((self.chunks_to_record * self.BUFFER_SIZE),
                                 dtype=numpy.int16)

    ### RECORDING AUDIO ###

    def __get_audio(self):
        """ Get a single buffer size of audio. """
        audio_string = self.in_stream.read(self.BUFFER_SIZE)
        return numpy.fromstring(audio_string, dtype=numpy.int16)

    def __close_recording(self):
        """ Cleanly back out and release sound card."""
        self.p.close(self.in_stream)

    def __init_recording(self):
        """ Initialize a recording. """
        self.in_stream = self.p.open(format=pyaudio.paInt16, channels=1,
                                     rate=self.RATE, input=True,
                                     frames_per_buffer=self.BUFFER_SIZE)

    def __record(self):
        """ Record sec_to_record seconds of audio."""
        self.__init_recording()
        while not self.__shutdown:
            for i in range(self.chunks_to_record):
                self.audio[i * self.BUFFER_SIZE:(i + 1) * self.BUFFER_SIZE] = self.__get_audio()
            self.new_audio = True
        self.__close_recording()

    def start(self):
        """ Start continuous recording in a new daemon thread. """
        recording_thread = threading.Thread(target=self.__record)
        recording_thread.daemon = True
        recording_thread.start()

    def stop(self):
        """ Shut down continuous recording."""
        self.__shutdown = True

    ### MATH ###

    @staticmethod
    def down_sample(data, mult):
        """ Given 1D data, return the binned average."""
        overhang = len(data) % mult
        if overhang:
            data = data[:-overhang]
        data = numpy.reshape(data, (len(data) / mult, mult))
        data = numpy.average(data, 1)
        return data

    def fft(self, data=None, trim_by=10, log_scale=False, div_by=100):
        if data is None:
            data = self.audio.flatten()
        left, right = numpy.split(numpy.abs(numpy.fft.fft(data)), 2)
        ys = numpy.add(left, right[::-1])
        if log_scale:
            ys = numpy.multiply(20, numpy.log10(ys))
        xs = numpy.arange(self.BUFFER_SIZE / 2, dtype=float)
        if trim_by:
            i = int((self.BUFFER_SIZE / 2) / trim_by)
            ys = ys[:i]
            xs = xs[:i] * self.RATE / self.BUFFER_SIZE
        if div_by:
            ys /= float(div_by)
        return xs, ys
