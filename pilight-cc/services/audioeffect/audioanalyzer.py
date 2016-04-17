""" Audio Analyser module. """

# PyGI - Audio recording and processing (Gst/GStreamer)
import re
from gi import require_version
from timeit import timeit

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

        self.__parser = Parser()

        self.__pipeline = Gst.Pipeline()

        # Audio source.
        self.__audio_source = Gst.ElementFactory.make("pulsesrc",
                                                      "audio_source")
        self.__audio_source.set_property("device", self.__source)
        # self.__audio_source = Gst.ElementFactory.make('audiotestsrc',
        #                                               "audio_source")
        # self.__audio_source.set_property('freq', 1000)
        self.__pipeline.add(self.__audio_source)

        self.__caps = Gst.caps_from_string(
            'audio/x-raw, rate=(int){0}, channels=(int){1}, depth=(int){2}'.format(
                AUDIOFREQ, 2 if self.__multichannel else 1, self.__depth))
        # self.__caps = Gst.caps_from_string(
        #     'audio/x-raw, channels=(int){0}'.format(2 if self.__multichannel else 1))
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

    # def parse_magnitude(self, msg):
    #     # Faster way to parse magnitudes
    #     return map(float, msg[msg.find('{') + 1:-3].split(','))


    #
    # def __parse_spectrum_message(self, msg):
    #     from re import sub
    #     from json import loads
    #     # First let's jsonize this
    #     # This is the message name, which we don't need
    #     text = msg.replace("spectrum, ", "")
    #     # name/value separator in json is : and not =
    #     text = text.replace("=", ": ")
    #     # Mutate the {} array notation from the structure to
    #     # [] notation for json.
    #     text = text.replace("{", "[")
    #     text = text.replace("}", "]")
    #     # Remove a few stray semicolons that aren't needed
    #     text = text.replace(";", "")
    #     # Remove the data type fields, as json doesn't need them
    #     text = sub(r"\(.+?\)", "", text)
    #     # double-quote the identifiers
    #     text = sub(r"([\w-]+):", r'"\1":', text)
    #     # Wrap the whole thing in brackets
    #     text = ("{" + text + "}")
    #     # Try to parse and return something sensible here, even if
    #     # the data was unparsable.
    #     try:
    #         return loads(text)
    #     except ValueError:
    #         return None

    def __on_message(self, _, msg):
        msg_st = msg.get_structure()
        # print msg.get_structure().to_string()
        if msg_st.get_name() == AudioAnalyser.__SPECTRUM_NAME and \
                msg_st.has_field(AudioAnalyser.__SPECTRUM_MAGNITUDE):
            print msg.get_structure().to_string()
            magnitudes = self.__parser.parse_spectrum_message(
                msg_st.to_string())
            if self.__multichannel:
                # TODO
                pass
            else:
                pass
                # self.__callback(msg.get_structure())

    def __on_eos(self, _):
        print("on_eos():")

    def __on_error(self, _, msg):
        print("on_error():", msg.parse_error())


def print_data(data):
    avg = sum(data) / len(data)
    stdout.write("Average amplitude: %d%%  dB \r" % (avg))
    stdout.flush()


class Parser(object):
    __MSG1 = "spectrum, endtime=(guint64)2500000000, timestamp=(guint64)2400000000, stream-time=(guint64)2400000000, running-time=(guint64)2400000000, duration=(guint64)100000000, magnitude=(float){ -28.070123672485352, -30.749044418334961, -33.143180847167969, -36.715190887451172, -40.343479156494141, -41.205394744873047, -41.560638427734375, -43.380313873291016, -46.788780212402344, -44.788078308105469, -42.305328369140625, -44.200847625732422, -40.548503875732422, -45.550392150878906, -46.724185943603516, -48.269428253173828, -51.178646087646484, -51.046237945556641, -49.490936279296875, -48.913726806640625, -49.530693054199219, -52.828620910644531, -52.078758239746094, -52.013782501220703, -52.997989654541016, -56.21478271484375, -55.835205078125, -56.219940185546875, -57.952301025390625, -62.604873657226562, -60.482810974121094, -58.831062316894531, -61.149932861328125, -61.567047119140625, -58.601184844970703, -60.795253753662109, -61.843009948730469, -63.226913452148438, -63.0216064453125, -61.332805633544922, -58.983997344970703, -58.646690368652344, -65.137275695800781, -64.511680603027344, -67.182647705078125, -66.760169982910156, -64.001670837402344, -66.311065673828125, -68.252510070800781, -65.517837524414062, -65.633865356445312, -66.019287109375, -65.434051513671875, -66.801239013671875, -68.136795043945312, -69.886146545410156, -71.071182250976562, -71.225425720214844, -68.818099975585938, -70.026008605957031, -66.050384521484375, -66.653907775878906, -66.2828369140625, -65.506828308105469, -66.304916381835938, -68.831565856933594, -68.145759582519531, -66.593887329101562, -65.731842041015625, -69.8892822265625, -68.144325256347656, -67.02142333984375, -69.02935791015625, -66.622467041015625, -68.351432800292969, -68.04571533203125, -70.514373779296875, -71.784934997558594, -69.944366455078125, -71.59356689453125, -68.998359680175781, -68.924209594726562, -71.486404418945312, -71.672943115234375, -71.02801513671875, -73.130470275878906, -73.786224365234375, -72.849273681640625, -73.184234619140625, -73.964820861816406, -75.090621948242188, -76.132926940917969, -75.9791259765625, -73.833259582519531, -76.507675170898438, -75.889350891113281, -74.05096435546875, -76.033271789550781, -74.589744567871094, -75.123558044433594, -76.096931457519531, -75.760726928710938, -78.022041320800781, -75.974090576171875, -77.533882141113281, -76.653663635253906, -76.268714904785156, -76.281829833984375, -77.650871276855469, -78.658660888671875, -78.417457580566406, -79.383338928222656, -78.981643676757812, -79.225387573242188, -79.512313842773438, -79.607864379882812, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80 };"
    __MSG2 = "spectrum, endtime=(guint64)1600000000, timestamp=(guint64)1500000000, stream-time=(guint64)1500000000, running-time=(guint64)1500000000, duration=(guint64)100000000, magnitude=(float)< < -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80 >, < -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80 > >;"

    def __init__(self):
        self.prog = re.compile(
            r'''magnitude=\(float\)[<{](?:(?: < (.*) > )| (.*) )[}>]''')
        self.prog2 = re.compile(r''' >, < ''')
        self.prog3 = re.compile(r''', ''')

    def bench1(self):
        self.parse_spectrum_message(Parser.__MSG1)

    def bench2(self):
        self.parse_spectrum_message(Parser.__MSG2)

    def parse_spectrum_message(self, msg):
        result = self.prog.search(msg)
        channels = self.prog2.split(
            result.group(1) if result.group(1) is not None else result.group(2))
        return [[float(s) for s in self.prog3.split(channel)] for channel
                in channels]


BANDS = 128
AUDIOFREQ = 44100.0
if __name__ == '__main__':
    print timeit("parser.bench1()",
                 "from __main__ import Parser; parser = Parser()", number=10000)
    print timeit("parser.bench2()",
                 "from __main__ import Parser; parser = Parser()", number=10000)
    # for i in range(0, BANDS):
    #     print "Freq index {} - {}".format(i, (
    #         (AUDIOFREQ / 2.0) * i + AUDIOFREQ / 4.0) / BANDS)
    # GObject.threads_init()
    # Gst.init(None)
    # AudioAnalyser(PULSE_AUDIO_DEVICE, print_data, bands=BANDS,
    #               multichannel=False).start()
    # Gtk.main()
