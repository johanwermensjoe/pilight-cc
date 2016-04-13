""" Audio Analyser module. """

# PyGI - Audio recording and processing (Gst/GStreamer)
from gi import require_version

require_version('Gst', '1.0')
require_version('Gtk', '3.0')
from gi.repository import Gst, Gtk, GObject

from threading import Thread
from sys import stdout

# PULSE_AUDIO_DEVICE = "alsa_output.pci-0000_00_1b.0.analog-stereo.monitor"
PULSE_AUDIO_DEVICE = "alsa_output.usb-Propellerhead_Balance_0001002008080-00.analog-stereo.monitor"


class AudioAnalyser:
    __SPECTRUM_NAME = "spectrum"
    __SPECTRUM_MAGNITUDE = 'magnitude'

    def __init__(self, source, callback, **opts):
        """
        Optional arguments:
            :param source: the PulseAudio device to capture
            :type source: str
            :param callback: the callback function for spectrum data
            :type callback: callable
            :param depth: the capture bit-depth (default: 16)
            :type depth: int
            :param bands: the number of spectrum bands (default: 128)
            :type bands: int
            :param amplify: magnitude amplification factor (default: 1)
            :type amplify: float
            :param threshold: the minimal magnitude in decibels (default: -80)
            :type threshold: float
            :param cutoff: the maximal magnitude in decibels (default: 1000)
            :type cutoff: float
            :param interval: the update interval in milliseconds (default: 100)
            :type interval: int
            :param multichannel: use multiple channels (default: False)
            :type multichannel: bool

        .. note:: The `callback` parameter should be a function my_callback(data),
          where `data` is a list of magnitudes for each `band` or nested lists if `multichannel` is ``True``.
        """
        self.__source = source
        self.__callback = callback
        self.__depth = opts.get('depth', 16)
        self.__bands = opts.get('bands', 128)
        self.__amplify = opts.get('bands', 1.0)
        self.__threshold = opts.get('threshold', -80)
        self.__cutoff = opts.get('cutoff', 100)
        self.__interval = opts.get('interval', 100)
        self.__multichannel = opts.get('multichannel', False)

        #  """
        #     <precision>     How many decimal places to round the magnitudes to
        #                     (default: 16).
        #     <amplify>       Amplify output by this much (default: 1).
        #     <logamplify>    Amplify magnitude values logarithmically to compensate for
        #                     softer higher frequencies.  (default: False)
        #     <autoamp>       Automatically control amplification levels when they are
        #                     too loud.
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
        #     <quiet>         Don't output to STDERR (default: False if no callback).
        # """
        #  self.running = False
        #  self.precision = opts.get('precision')
        #  self.logamplify = opts.get('logamplify', False)
        #  self.autoamp = opts.get('autoamp', False)
        #  self.scaleto = opts.get('scale', 100)
        #  self.raw = opts.get('raw', True)
        #  self.db = opts.get('db', False)
        #  self.iec = opts.get('iec', False)
        #  self.vumeter = opts.get('vumeter', False)
        #  self.bands_cutoff = opts.get('cutoff', 96)
        #  self.quiet = opts.get('quiet', self.callback is not None)
        #  self.gainhits = 0
        #  self.origamp = self.amplify

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

        self.__pipeline = Gst.Pipeline()

        # Audio source.
        # self.__audio_source = Gst.ElementFactory.make("pulsesrc", "audio_source")
        # self.__audio_source.set_property("device", self.__source)
        self.__audio_source = Gst.ElementFactory.make('audiotestsrc',
                                                      "audio_source")
        self.__audio_source.set_property('freq', 1000)
        self.__pipeline.add(self.__audio_source)

        self.__caps = Gst.caps_from_string(
            'audio/x-raw, rate=(int){0}'.format(AUDIOFREQ))
        self.__caps_filter = Gst.ElementFactory.make('capsfilter', "filter")
        self.__caps_filter.set_property('caps', self.__caps)
        self.__pipeline.add(self.__caps_filter)

        # Spectrum analyser.
        self.__spectrum_analyser = Gst.ElementFactory.make('spectrum',
                                                           "spectrum_analyser")
        self.__spectrum_analyser.set_property('bands', self.__bands)
        self.__spectrum_analyser.set_property('interval',
                                              self.__interval * 1000000)
        self.__spectrum_analyser.set_property('threshold', self.__threshold)
        self.__spectrum_analyser.set_property('multi-channel',
                                              self.__multichannel)
        self.__pipeline.add(self.__spectrum_analyser)

        # Sink
        self.__sink = Gst.ElementFactory.make('fakesink', "sink")
        self.__pipeline.add(self.__sink)

        # Messages.
        self.__bus = self.__pipeline.get_bus()
        self.__bus.add_signal_watch()
        self.__connections = [
            self.__bus.connect('message::eos', self.__on_eos),
            self.__bus.connect('message::error', self.__on_error),
            self.__bus.connect('message::element', self.__on_message)
        ]

        # Link
        # self.__audio_source.link(self.__spectrum_analyser)
        # self.__caps = Gst.caps_from_string('audio/x-raw, rate=(int){0}'.format(AUDIOFREQ))
        # self.__audio_source.link_filtered(self.__spectrum_analyser, self.__caps)
        self.__audio_source.link(self.__caps_filter)
        self.__caps_filter.link(self.__spectrum_analyser)
        self.__spectrum_analyser.link(self.__sink)

    def __del__(self):
        self.stop()

    def start(self):
        self.__pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.__bus.dissconnect(self.__connections)
        self.__bus.remove_signal_watch()
        self.__pipeline.set_state(Gst.State.NULL)

    def __on_message(self, _, msg):
        msg_st = msg.get_structure()
        if msg_st.get_name() == AudioAnalyser.__SPECTRUM_NAME and \
                msg_st.has_field(AudioAnalyser.__SPECTRUM_MAGNITUDE):
            if self.__multichannel:
                # TODO
                pass
            else:
                print msg.get_structure().to_string()
                # self.__callback(msg.get_structure())

    def __on_eos(self, _):
        print("on_eos():")

    def __on_error(self, _, msg):
        print("on_error():", msg.parse_error())

def print_data(data):
    avg = sum(data) / len(data)
    stdout.write("Average amplitude: %d%%  dB \r" % (avg))
    stdout.flush()

BANDS = 256
AUDIOFREQ = 22050.0
if __name__ == '__main__':
    for i in range(0, BANDS):
        print "Freq index {} - {}".format(i, ((AUDIOFREQ / 2.0) * i + AUDIOFREQ / 4.0) / BANDS)
    GObject.threads_init()
    Gst.init(None)
    AudioAnalyser(PULSE_AUDIO_DEVICE, print_data, bands=BANDS).start()
    Gtk.main()
