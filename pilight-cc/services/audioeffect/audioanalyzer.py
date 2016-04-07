""" Audio Analyser module. """

# PyGI - Audio recording and processing (Gst/GStreamer)
from gi import require_version

require_version('Gst', '1.0')
require_version('Gtk', '3.0')
from gi.repository import Gst, Gtk, GObject

from threading import Thread

PULSE_AUDIO_DEVICE = "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"


class AudioAnalyser:

    __SPECTRUM_MSG = "spectrum"

    def __init__(self, **opts):
        """ Constructor

        Optional arguments:
            :param device: the PulseAudio device to capture
            :type device: str
            :param bands: the number of spectrum bands (default: 128)
            :type bands: int
            :param threshold: the minimal magnitude in decibels (default: -80)
            :type threshold: int
            :param interval: the update interval in milliseconds (default: 100)
            :type interval: int
            :param multichannel: use multiple channels (default: False)
            :type multichannel: bool
            :param callback: the callback for spectrum data (default: None)
            :type callback: callable

        Example:

        >>> def my_callback(data):
        >>>    ...
        >>>
        >>> Main(callback = my_callback)

        """
        AudioAnalyser()
       #  """
       #     <source>        Source of the audio (default: alsasrc or gconf setting).
       #     <precision>     How many decimal places to round the magnitudes to
       #                     (default: 16).
       #     <bands>         How many frequency bands to output (default: 128).
       #     <amplify>       Amplify output by this much (default: 1).
       #     <logamplify>    Amplify magnitude values logarithmically to compensate for
       #                     softer higher frequencies.  (default: False)
       #     <autoamp>       Automatically control amplification levels when they are
       #                     too loud.
       #     <threshold>     Minimal magnitude of a band in decibels (default: 70).
       #     <cufoff>        Cut off magnitudes at this value after amplification has
       #                     been applied (default: 100).
       #     <scale>         Scale magnitudes to this value (default: 100).
       #     <raw>           Don't clip or apply logarithmic upscale the output.
       #                     (default: True).
       #     <db>            Return output in decibels instead of a percentage.
       #                     <logamplify> is ignored (default: False).
       #     <iec>           Convert decibels to percentages with IEC 60268-18 scaling
       #                     (default: False).
       #     <vumeter>       Return VU meter output instead of spectrum.  <bands>
       #                     controls how many channels to output here.  <threshold> is
       #                     ignored.
       #     <interval>      Milliseconds to wait between polls (default: 50).
       #     <multichannel>  Spectrum from multiple channels? (default: False)
       #     <quiet>         Don't output to STDERR (default: False if no callback).
       #     <callback>      Return the magnitude list to this function (default: None).
       # """
       #  self.running = False
       #  self.source = opts.get('source')
       #  self.precision = opts.get('precision')
       #  self.bands = opts.get('bands', 128)
       #  self.amplify = opts.get('amplify', 1)
       #  self.logamplify = opts.get('logamplify', False)
       #  self.autoamp = opts.get('autoamp', False)
       #  self.threshold = opts.get('threshold', 70)
       #  self.cutoff = opts.get('cutoff', 100)
       #  self.scaleto = opts.get('scale', 100)
       #  self.raw = opts.get('raw', True)
       #  self.db = opts.get('db', False)
       #  self.iec = opts.get('iec', False)
       #  self.vumeter = opts.get('vumeter', False)
       #  self.interval = opts.get('interval', 50)
       #  self.callback = opts.get('callback')
       #  self.multichannel = opts.get('multichannel', False)
       #  self.bands_cutoff = opts.get('cutoff', 96)
       #  self.quiet = opts.get('quiet', self.callback is not None)
       #  self.pipeline = None
       #  self.gainhits = 0
       #  self.origamp = self.amplify
       #  self.__pipeline = Gst.Pipeline()

        # self.autoaudiosrc = Gst.ElementFactory.make("pulsesrc", "audio")
        # self.autoaudiosrc.set_property("device", PULSE_AUDIO_DEVICE)
        # self.audioconvert = Gst.ElementFactory.make("audioconvert", "audioconv")
        # self.audioresample = Gst.ElementFactory.make("audioresample",
        #                                         "audioresample")
        # self.vorbisenc = Gst.ElementFactory.make("vorbisenc", "vorbisenc")
        # self.oggmux = Gst.ElementFactory.make("oggmux", "oggmux")
        # self.filesink = Gst.ElementFactory.make("filesink", "filesink")
        #
        # self.audioresample.set_property("quality", 10)
        # self.vorbisenc.set_property("quality", 1)
        #
        # self.filesink.set_property("location", "test.ogg")
        # self.__pipeline.add(self.autoaudiosrc)
        # self.__pipeline.add(self.audioconvert)
        # self.__pipeline.add(self.vorbisenc)
        # self.__pipeline.add(self.oggmux)
        # self.__pipeline.add(self.filesink)
        # self.__pipeline.add(self.audioresample)
        #
        # self.autoaudiosrc.link(self.audioconvert)
        # self.audioconvert.link(self.audioresample)
        # self.audioresample.link(self.vorbisenc)
        # self.vorbisenc.link(self.oggmux)
        # self.oggmux.link(self.filesink)

        self.__audio_source = Gst.ElementFactory.make("audiotestsrc",
                                                      "audio_source")
        self.__audio_source.set_property("freq", 1000)
        # self.__audio_source = Gst.ElementFactory.make("pulsesrc", "audio_source")
        # self.__audio_source.set_property("device", PULSE_AUDIO_DEVICE)
        self.__pipeline.add(self.__audio_source)

        self.__spectrum_analyser = Gst.ElementFactory.make("spectrum",
                                                           "spectrum_analyser")
        self.__spectrum_analyser.set_property("bands", )
        self.__pipeline.add(self.__spectrum_analyser)

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message::eos', self.__on_eos)
        self.bus.connect('message::error', self.__on_error)
        self.bus.connect('message::element', self.__on_message)

        self.__audio_source.link(self.__spectrum_analyser)

        self.__pipeline.set_state(Gst.State.PLAYING)

    def __on_message(self, _, msg):
        if msg.get_structure().get_name() == Main.__SPECTRUM_MSG:
            print('spectrum msg')

    def __on_eos(self, _):
        print("on_eos():")

    def __on_error(self, _, msg):
        print("on_error():", msg.parse_error())

    # def on_message(self, bus, message):
    #     # We should return false if the pipeline has stopped
    #     if not self.running:
    #         return False
    #
    #     try:
    #         # s = message.structure
    #         s = message.get_structure()
    #         if not s:
    #             return
    #         name = s.get_name()
    #
    #         if name == 'spectrum' and s.has_field('magnitude'):
    #
    #             # mags = s.get_value('magnitude')
    #
    #             # PyGI doesn't fully support spectrum yet: https://bugzilla.gnome.org/show_bug.cgi?id=693168
    #
    #             if self.multichannel:
    #                 mags = self.parse_spectrum_structure(s.to_string())['magnitude']
    #                 magnitudes = mags[0][
    #                              :self.bands_cutoff]  # We use only the first channel for now
    #             else:
    #                 mags = self.parse_magnitude(s.to_string())
    #                 magnitudes = mags[:self.bands_cutoff]
    #
    #             if not self.db:
    #                 if self.logamplify:
    #                     magnitudes = [self.dbtopct(db, i) for i, db
    #                                   in enumerate(magnitudes)]
    #                 else:
    #                     magnitudes = [self.dbtopct(db) for i, db
    #                                   in enumerate(magnitudes)]
    #             if not self.raw:
    #                 magnitudes = self.scale(magnitudes, self.bands)
    #             magnitudes = [self.round(m) for m in magnitudes]
    #         elif name == 'level' and s.has_field('peak') and s.has_field('decay'):
    #             magnitudes = []
    #             peaks = s.get_value('peak')
    #             decays = s.get_value('decay')
    #             for channel in range(0, min(self.bands, len(peaks))):
    #                 peak = max(-self.threshold, min(0, peaks[channel]))
    #                 decay = max(-self.threshold, min(0, decays[channel]))
    #                 if not self.db:
    #                     if self.logamplify:
    #                         peak = self.dbtopct(peak, peak)
    #                         decay = self.dbtopct(decay, decay)
    #                     else:
    #                         peak = self.dbtopct(peak)
    #                         decay = self.dbtopct(decay)
    #                 magnitudes.append(self.round(peak))
    #                 magnitudes.append(self.round(decay))
    #         else:
    #             return True
    #         if not self.quiet:
    #             try:
    #                 print(' | '.join(('%.3f' % m for m in magnitudes)))
    #             except IOError:
    #                 self.loop.quit()
    #
    #         if self.callback:
    #             self.callback(magnitudes)
    #     except KeyboardInterrupt:
    #         self.loop.quit()
    #     return True

    # @staticmethod
    # def down_sample(data, mult):
    #     """ Given 1D data, return the binned average."""
    #     overhang = len(data) % mult
    #     if overhang:
    #         data = data[:-overhang]
    #     data = numpy.reshape(data, (len(data) / mult, mult))
    #     data = numpy.average(data, 1)
    #     return data
    #
    # def fft(self, data=None, trim_by=10, log_scale=False, div_by=100):
    #     if data is None:
    #         data = self.__audio.flatten()
    #     left, right = numpy.split(numpy.abs(numpy.fft.fft(data)), 2)
    #     ys = numpy.add(left, right[::-1])
    #     if log_scale:
    #         ys = numpy.multiply(20, numpy.log10(ys))
    #     xs = numpy.arange(AudioRecorder.__BUFFER_SIZE / 2, dtype=float)
    #     if trim_by:
    #         i = int((AudioRecorder.__BUFFER_SIZE / 2) / trim_by)
    #         ys = ys[:i]
    #         xs = xs[:i] * AudioRecorder.__RATE / AudioRecorder.__BUFFER_SIZE
    #     if div_by:
    #         ys /= float(div_by)
    #     return xs, ys
    #
    # @staticmethod
    # def list_devices():
    #     # List all audio input devices
    #     pp = pyaudio.PyAudio()
    #     i = 0
    #     n = pp.get_device_count()
    #     while i < n:
    #         dev = pp.get_device_info_by_index(i)
    #         if dev['maxInputChannels'] > 0:
    #             print str(i)+'. '+dev['name']
    #         else:
    #             print str(i)+'. '+dev['name']
    #         i += 1

if __name__ == '__main__':
    GObject.threads_init()
    Gst.init(None)
    AudioAnalyser()
    Gtk.main()

