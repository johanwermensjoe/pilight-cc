""" Audio Analyser module. """

# PyGI - Audio recording and processing (Gst/GStreamer)
from gi import require_version

from pilightcc.util.error import BaseError

require_version('Gst', '1.0')
require_version('Gtk', '3.0')
from gi.repository import Gst, GObject

from threading import Thread, Lock


class AudioAnalyser:
    __LEVEL_MSG_NAME = 'level'
    __LEVEL_MSG_RMS = 'rms'
    __LEVEL_MSG_PEAK = 'peak'
    __LEVEL_MSG_DECAY = 'decay'

    __SPECTRUM_MSG_NAME = 'spectrum'
    __SPECTRUM_MSG_MAGNITUDE = 'magnitude'

    class Mode(object):
        SPECTRUM = 'spectrum'
        LEVEL = 'level'

    def __init__(self, source, callback, **opts):
        """
        Optional arguments:

            :param source: the PulseAudio device to capture
            :type source: str
            :param callback: the callback function for spectrum data
            :type callback: callable
            :param error_callback: the error callback function (default: None)
            :type error_callback: callable
            :param mode: the analyser mode (default: SPECTRUM)
            :type mode: Mode
            :param depth: the capture bit-depth (default: 16)
            :type depth: int
            :param bands: the number of spectrum bands 'SPECTRUM' (default: 128)
            :type bands: int
            :param min_band: the minimum band index (default: 0)
            :type min_band: int
            :param max_band: the maximum band index (default: `bands` - 1)
            :type max_band: int
            :param amplify: magnitude amplification factor (default: 1)
            :type amplify: float
            :param threshold: the minimal magnitude in dB (default: -80)
            :type threshold: float
            :param cutoff: the maximal magnitude in dB (default: 1000)
            :type cutoff: float
            :param interval: the update interval in ms (default: 100)
            :type interval: int
            :param multichannel: use multiple channels (default: False)
            :type multichannel: bool
            :param samplerate: the sample rate to use (default: 48000)
            :type samplerate: int
            :param peak_ttl: the peak ttl in ms 'LEVEL' (default: 30)
            :type peak_ttl: float
            :param peak_falloff: the peak falloff in dB/s 'LEVEL' (default: 10)
            :type peak_falloff: float

        Tips:

        * The `samplerate` parameter decides the upper frequency
          bound (`samplerate` / 2) of the spectrum data.

        * The `callback` parameter should be a function
          my_callback(data), where `data` is a list of magnitudes
          for each `band` or nested lists if `multichannel` is ``True``.

        * The `error_callback` parameter should be a function
          my_error_callback(msg), where `msg` is a error message.
        """
        self.__running = False
        self.__lock = Lock()
        self.__source = source
        self.__callback = callback
        self.__error_callback = opts.get('error_callback', None)
        self.__mode = opts.get('mode', self.Mode.SPECTRUM)
        self.__depth = opts.get('depth', 16)
        self.__bands = opts.get('bands', 128)
        self.__min_band = opts.get('min_band', 0)
        self.__max_band = opts.get('max_band', self.__bands - 1)
        self.__amplify = opts.get('bands', 1.0)
        self.__threshold = opts.get('threshold', -80)
        self.__cutoff = opts.get('cutoff', 100)
        self.__interval = opts.get('interval', 100)
        self.__multichannel = opts.get('multichannel', False)
        self.__sample_rate = opts.get('samplerate', 48000)
        self.__peak_ttl = opts.get('peak_ttl', 30)
        self.__peak_falloff = opts.get('peak_falloff', 10)

        #  """
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
        # """
        #  self.logamplify = opts.get('logamplify', False)
        #  self.autoamp = opts.get('autoamp', False)
        #  self.scaleto = opts.get('scale', 100)
        #  self.raw = opts.get('raw', True)
        #  self.db = opts.get('db', False)
        #  self.iec = opts.get('iec', False)
        #  self.gainhits = 0
        #  self.origamp = self.amplify

        # Initiate gobject.
        GObject.threads_init()
        Gst.init(None)
        self.__loop = GObject.MainLoop()

        self.__parser = SpectrumParser()

        self.__pipeline = Gst.Pipeline()

        if self.__mode == self.Mode.LEVEL:
            self.__setup_level_analyser()
        else:
            self.__setup_spectrum_analyser()

        # Messages.
        self.__bus = self.__pipeline.get_bus()
        self.__connections = []

    def __del__(self):
        self.stop()

    def __setup_spectrum_analyser(self):
        # Audio source.
        audio_source = Gst.ElementFactory.make('pulsesrc', None)
        audio_source.set_property('device', self.__source)
        # audio_source = Gst.ElementFactory.make('audiotestsrc', None)
        # audio_source.set_property('freq', 1000)
        self.__pipeline.add(audio_source)

        caps = Gst.caps_from_string(
            "audio/x-raw, channels=(int){}, rate=(int){}".format(
                2 if self.__multichannel else 1, self.__sample_rate))
        caps_filter = Gst.ElementFactory.make('audioconvert', None)
        self.__pipeline.add(caps_filter)

        # Spectrum analyser.
        spectrum_analyser = Gst.ElementFactory.make('spectrum', None)
        spectrum_analyser.set_property('bands', self.__bands)
        spectrum_analyser.set_property('interval',
                                       self.__interval * Gst.MSECOND)
        spectrum_analyser.set_property('threshold', self.__threshold)
        spectrum_analyser.set_property('multi-channel', self.__multichannel)
        self.__pipeline.add(spectrum_analyser)

        # Sink
        sink = Gst.ElementFactory.make('fakesink', None)
        self.__pipeline.add(sink)

        # Link
        audio_source.link(caps_filter)
        caps_filter.link_filtered(spectrum_analyser, caps)
        spectrum_analyser.link(sink)

    def __setup_level_analyser(self):
        # Audio source.
        audio_source = Gst.ElementFactory.make('pulsesrc', None)
        audio_source.set_property('device', self.__source)
        self.__pipeline.add(audio_source)

        caps = Gst.caps_from_string(
            "audio/x-raw, channels=(int){}, rate=(int){}".format(
                2 if self.__multichannel else 1, self.__sample_rate))
        caps_filter = Gst.ElementFactory.make('audioconvert', None)
        self.__pipeline.add(caps_filter)

        # Level messages.
        level_analyser = Gst.ElementFactory.make('level', None)
        level_analyser.set_property('interval', self.__interval * Gst.MSECOND)
        level_analyser.set_property('peak-falloff',
                                    self.__peak_falloff)
        level_analyser.set_property('peak-ttl', self.__peak_ttl * Gst.MSECOND)
        self.__pipeline.add(level_analyser)

        # Sink
        sink = Gst.ElementFactory.make('fakesink', None)
        self.__pipeline.add(sink)

        # Link
        audio_source.link(caps_filter)
        caps_filter.link_filtered(level_analyser, caps)
        level_analyser.link(sink)

    def __on_message(self, _, msg):
        msg_st = msg.get_structure()
        if msg_st.get_name() == AudioAnalyser.__SPECTRUM_MSG_NAME:
            # TODO Possible optimize parsing with min/max index.
            if self.__multichannel:
                magnitudes = self.__parser.parse_multi_channel_message(
                    msg_st.to_string())
            else:
                magnitudes = self.__parser.parse_single_channel_message(
                    msg_st.to_string())
            # print(self.__audio_source.get_property("stream-properties"))
            # print(self.__audio_source.get_property("device-name"))
            # print(self.__audio_source.get_property("mute"))
            # print(self.__audio_source.get_property("volume"))
            # print(self.__audio_source.get_property("client-name"))
            # print(self.__audio_source.get_property("current-device"))
            # print(self.__audio_source.get_property("device"))
            self.__callback(magnitudes[self.__min_band:self.__max_band])
        elif msg_st.get_name() == AudioAnalyser.__LEVEL_MSG_NAME:
            self.__callback({
                'rms': msg_st.get_value(
                    AudioAnalyser.__LEVEL_MSG_RMS),
                'peak': msg_st.get_value(
                    AudioAnalyser.__LEVEL_MSG_PEAK),
                'decay': msg_st.get_value(
                    AudioAnalyser.__LEVEL_MSG_DECAY)
            })
        else:
            print(msg_st.to_string())

    def __on_eos(self, _):
        self.stop()
        self.__error_callback("Gst error: EOS")

    def __on_error(self, _, msg):
        self.stop()
        self.__error_callback("Gst error: {}".format(msg.parse_error()))
        # TODO Remove print
        print("on_error():", msg.parse_error())

    def start(self):
        """ Start analysing audio.
        """
        with self.__lock:
            if not self.__running:
                self.__running = True

                # Setup signals.
                self.__bus.add_signal_watch()
                self.__connections = [
                    self.__bus.connect('message::eos', self.__on_eos),
                    self.__bus.connect('message::error', self.__on_error),
                    self.__bus.connect('message::element', self.__on_message)
                ]
                self.__pipeline.set_state(Gst.State.PLAYING)

                # Setup shutdown watcher and start main loop.
                Thread(target=self.__loop.run).start()

    def stop(self):
        """ Stop analysing audio.
        """
        with self.__lock:
            if self.__running:
                self.__running = False
                self.__loop.quit()

                # Disconnect and set state.
                [self.__bus.disconnect(c) for c in self.__connections]
                self.__bus.remove_signal_watch()
                self.__pipeline.set_state(Gst.State.NULL)

    def is_running(self):
        """
        The running status.
            :return: True if the analyser is running.
            :rtype: bool
        """
        with self.__lock:
            return self.__running

    def print_band_frequencies(self):
        """ Print the frequency range corresponding to each band.
        """
        for i in range(0, self.__bands):
            print "Freq index {} -> {} - {}".format(
                i, ((self.__sample_rate / 2.0) / self.__bands) * i,
                   ((self.__sample_rate / 2.0) / self.__bands) * (i + 1))


class AudioAnalyserError(BaseError):
    """ Error raised for audio analysis errors.
    """

    def __init__(self, msg):
        """
            :param msg: the error message
            :type msg: str
        """
        self.msg = msg


class SpectrumParser(object):
    _MSG1 = "spectrum, endtime=(guint64)2500000000, timestamp=(guint64)2400000000, stream-time=(guint64)2400000000, running-time=(guint64)2400000000, duration=(guint64)100000000, magnitude=(float){ -28.070123672485352, -30.749044418334961, -33.143180847167969, -36.715190887451172, -40.343479156494141, -41.205394744873047, -41.560638427734375, -43.380313873291016, -46.788780212402344, -44.788078308105469, -42.305328369140625, -44.200847625732422, -40.548503875732422, -45.550392150878906, -46.724185943603516, -48.269428253173828, -51.178646087646484, -51.046237945556641, -49.490936279296875, -48.913726806640625, -49.530693054199219, -52.828620910644531, -52.078758239746094, -52.013782501220703, -52.997989654541016, -56.21478271484375, -55.835205078125, -56.219940185546875, -57.952301025390625, -62.604873657226562, -60.482810974121094, -58.831062316894531, -61.149932861328125, -61.567047119140625, -58.601184844970703, -60.795253753662109, -61.843009948730469, -63.226913452148438, -63.0216064453125, -61.332805633544922, -58.983997344970703, -58.646690368652344, -65.137275695800781, -64.511680603027344, -67.182647705078125, -66.760169982910156, -64.001670837402344, -66.311065673828125, -68.252510070800781, -65.517837524414062, -65.633865356445312, -66.019287109375, -65.434051513671875, -66.801239013671875, -68.136795043945312, -69.886146545410156, -71.071182250976562, -71.225425720214844, -68.818099975585938, -70.026008605957031, -66.050384521484375, -66.653907775878906, -66.2828369140625, -65.506828308105469, -66.304916381835938, -68.831565856933594, -68.145759582519531, -66.593887329101562, -65.731842041015625, -69.8892822265625, -68.144325256347656, -67.02142333984375, -69.02935791015625, -66.622467041015625, -68.351432800292969, -68.04571533203125, -70.514373779296875, -71.784934997558594, -69.944366455078125, -71.59356689453125, -68.998359680175781, -68.924209594726562, -71.486404418945312, -71.672943115234375, -71.02801513671875, -73.130470275878906, -73.786224365234375, -72.849273681640625, -73.184234619140625, -73.964820861816406, -75.090621948242188, -76.132926940917969, -75.9791259765625, -73.833259582519531, -76.507675170898438, -75.889350891113281, -74.05096435546875, -76.033271789550781, -74.589744567871094, -75.123558044433594, -76.096931457519531, -75.760726928710938, -78.022041320800781, -75.974090576171875, -77.533882141113281, -76.653663635253906, -76.268714904785156, -76.281829833984375, -77.650871276855469, -78.658660888671875, -78.417457580566406, -79.383338928222656, -78.981643676757812, -79.225387573242188, -79.512313842773438, -79.607864379882812, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80 };"
    _MSG2 = "spectrum, endtime=(guint64)1600000000, timestamp=(guint64)1500000000, stream-time=(guint64)1500000000, running-time=(guint64)1500000000, duration=(guint64)100000000, magnitude=(float)< < -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80 >, < -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80, -80 > >;"

    def __init__(self):
        import re
        """ Compile regex """
        self.magnitude_parse = re.compile(
            r'''magnitude=\(float\)[<{](?:(?: < (.*) > )| (.*) )[}>]''')
        self.channel_parse = re.compile(r''' >, < ''')
        self.value_parse = re.compile(r''',''')

    def parse_message(self, msg):
        """
        Parse any type of spectrum message.
            :param msg: the spectrum message
            :type msg: str
            :return: a nested list of channels and band magnitudes in dB
            :rtype: list
        .. note:: Slower than the specialized functions.
        """
        result = self.magnitude_parse.search(msg)
        channels = self.channel_parse.split(
            result.group(1) if result.group(1) is not None else result.group(2))
        return [[float(s) for s in self.value_parse.split(channel)] for channel
                in channels]

    @staticmethod
    def parse_single_channel_message(msg):
        """
        Parse a multi channel spectrum message.
            :param msg: the spectrum message
            :type msg: str
            :return: a nested list of one channel with band magnitudes in dB
            :rtype: list
        """
        return [map(float, msg[msg.find('{') + 1:-3].split(','))]

    @staticmethod
    def parse_multi_channel_message(msg):
        """
        Parse a multi channel spectrum message.
            :param msg: the spectrum message
            :type msg: str
            :return: a nested list of one channel with band magnitudes in dB
            :rtype: list
        """
        return [map(float, v.split(',')) for v in
                msg[msg.find('<') + 4:-5].split('>, <')]


def print_data(data):
    from sys import stdout
    if len(data) > 3:
        stdout.write("\rAmplitude: %d%%  dB" % (data[0][1]))
    else:
        stdout.write("\rRMS: {}  dB, Peak: {}  dB, Decay: {}  dB"
                     .format(data['rms'], data['peak'], data['decay']))
    stdout.flush()


if __name__ == '__main__':
    PULSE_AUDIO_DEVICE = "alsa_output.usb-Propellerhead_Balance_0001002008080-00.analog-stereo.monitor"
    aa = AudioAnalyser(PULSE_AUDIO_DEVICE, print_data, bands=128,
                       multichannel=False, interval=100,
                       mode=AudioAnalyser.Mode.LEVEL)
    aa.start()
    from time import sleep

    while True:
        sleep(1)
