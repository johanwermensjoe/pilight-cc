""" Audio Analyser module. """

# PyGI - Audio recording and processing (Gst/GStreamer)
from gi import require_version

from pilightcc.util.error import BaseError

require_version('Gst', '1.0')
require_version('Gtk', '3.0')
from gi.repository import Gst, GObject

from threading import Thread, Lock


class BaseAudioAnalyser:
    def __init__(self, error_callback=None):
        self.__running = False
        self.__lock = Lock()
        self.__error_callback = error_callback

        # Initiate GObject.
        GObject.threads_init()
        Gst.init(None)
        self.__loop = GObject.MainLoop()
        self.__pipelines = []
        self.__connections = []

    def __del__(self):
        self.stop()

    def _on_eos(self, _):
        self.stop()
        if self.__error_callback is not None:
            self.__error_callback("Gst error: EOS")
        print("on_eos():")  # TODO Remove print

    def _on_error(self, _, msg):
        msg_st = msg.get_structure()
        self.stop()
        if self.__error_callback is not None:
            self.__error_callback("Gst error: {}".format(msg_st.to_string()))
        print("on_error():", msg_st.to_string())  # TODO Remove print

    def _register_virtual_pipeline(self, pipeline):
        self.__pipelines.append(pipeline.compile())

    def start(self):
        """ Start analysing audio.
        """
        with self.__lock:
            if not self.__running:
                self.__running = True

                # Connect handlers and set state.
                for p, handlers in self.__pipelines:
                    bus = p.get_bus()
                    bus.add_signal_watch()
                    handler_connections = [bus.connect(tag, handler) for
                                           tag, handler in handlers]
                    self.__connections.append((p, handler_connections))

                for p, _ in self.__pipelines:
                    p.set_state(Gst.State.PLAYING)

                # Setup shutdown watcher and start main loop.
                Thread(target=self.__loop.run).start()

    def stop(self):
        """ Stop analysing audio.
        """
        with self.__lock:
            if self.__running:
                self.__running = False
                self.__loop.quit()

                # Disconnect handlers and set state.
                for p, handler_connections in self.__connections:
                    bus = p.get_bus()
                    [bus.disconnect(c) for c in handler_connections]
                    bus.remove_signal_watch()
                    p.set_state(Gst.State.NULL)

    def is_running(self):
        """
        The running status.
            :return: True if the analyser is running.
            :rtype: bool
        """
        with self.__lock:
            return self.__running


class AudioAnalyserError(BaseError):
    """ Error raised for audio analysis errors.
    """

    def __init__(self, msg):
        """
            :param msg: the error message
            :type msg: str
        """
        self.msg = msg


class LevelAudioAnalyser(BaseAudioAnalyser):
    __LEVEL_MSG_NAME = 'level'
    __LEVEL_MSG_RMS = 'rms'
    __LEVEL_MSG_PEAK = 'peak'
    __LEVEL_MSG_DECAY = 'decay'

    class MessageTag(object):
        LOW = 'low'
        MID = 'mid'
        HIGH = 'high'

    def __init__(self, source, callback, **opts):
        """
        Optional arguments:

            :param source: the PulseAudio device to capture
            :type source: str
            :param callback: the callback function for spectrum data
            :type callback: callable
            :param error_callback: the error callback function (default: None)
            :type error_callback: callable
            :param interval: the update interval in ms (default: 100)
            :type interval: int
            :param multichannel: use multiple channels (default: False)
            :type multichannel: bool
            :param samplerate: the sample rate to use in Hz (default: 44100)
            :type samplerate: int
            :param peak_ttl: the peak ttl in ms 'LEVEL' (default: 30)
            :type peak_ttl: float
            :param peak_falloff: the peak falloff in dB/s 'LEVEL' (default: 10)
            :type peak_falloff: float

        Tips:

        * The `samplerate` parameter decides the upper frequency bound.

        * The `callback` parameter should be a function
          my_callback(data), where `data` is a dict of . # TODO

        * The `error_callback` parameter should be a function
          my_error_callback(msg), where `msg` is a error message.
        """
        BaseAudioAnalyser.__init__(self, opts.get('error_callback', None))
        self.__source = source
        self.__callback = callback
        self.__interval = opts.get('interval', 100)
        self.__multichannel = opts.get('multichannel', False)
        self.__sample_rate = opts.get('samplerate', 44100)
        self.__peak_ttl = opts.get('peak_ttl', 30)
        self.__peak_falloff = opts.get('peak_falloff', 10)

        # Create pipelines.
        self.__level_lock = Lock()
        self.__levels = {}
        self.__initialized = False

        low_pipeline = self.__create_filter_pipeline(
            lambda _, m: self.__on_message(self.MessageTag.LOW, _, m))
        low_pipeline.add_limit_filter(100, 'low-pass')
        self._register_virtual_pipeline(low_pipeline)

        mid_pipeline = self.__create_filter_pipeline(
            lambda _, m: self.__on_message(self.MessageTag.MID, _, m))
        mid_pipeline.add_band_filter(1000, 4500, 'band-pass')
        self._register_virtual_pipeline(mid_pipeline)

        high_pipeline = self.__create_filter_pipeline(
            lambda _, m: self.__on_message(self.MessageTag.HIGH, _, m))
        high_pipeline.add_limit_filter(5000, 'high-pass')
        self._register_virtual_pipeline(high_pipeline)

    def __create_filter_pipeline(self, handler):
        return FilterLevelPipeline(self.__source, self.__multichannel,
                                   self.__sample_rate, self.__interval,
                                   self.__peak_falloff, self.__peak_ttl,
                                   handler, self._on_error, self._on_eos)

    def __on_message(self, tag, _, msg):
        msg_st = msg.get_structure()
        if msg_st.get_name() == LevelAudioAnalyser.__LEVEL_MSG_NAME:
            with self.__level_lock:
                self.__levels[tag] = {
                    'rms': msg_st.get_value(
                        LevelAudioAnalyser.__LEVEL_MSG_RMS),
                    'peak': msg_st.get_value(
                        LevelAudioAnalyser.__LEVEL_MSG_PEAK),
                    'decay': msg_st.get_value(
                        LevelAudioAnalyser.__LEVEL_MSG_DECAY)
                }

            if not self.__initialized:
                self.__initialized = all([tag in self.__levels
                                          for tag in [self.MessageTag.LOW,
                                                      self.MessageTag.MID,
                                                      self.MessageTag.HIGH]])

            # print("{}: {}".format(tag, msg_st.to_string()))
            if self.MessageTag.LOW == tag and self.__initialized:
                self.__callback(
                    {self.MessageTag.LOW: self.__levels[self.MessageTag.LOW],
                     self.MessageTag.MID: self.__levels[self.MessageTag.MID],
                     self.MessageTag.HIGH: self.__levels[self.MessageTag.HIGH]})
        else:
            print(msg_st.to_string())


def print_data(data):
    if len(data) > 3:
        # from sys import stdout
        # stdout.write("\rAmplitude: %d%%  dB" % (data[0][1]))
        # stdout.flush()
        print("Amplitude: %d%%  dB" % (data[0][1]))
    else:
        print(data)


class BaseVirtualPipeline(object):
    def __init__(self, on_error, on_eos):
        self.elements = []
        self.handlers = [('message::eos', on_eos), ('message::error', on_error)]

    def _link_elements(self):
        """ To be implemented by subclass.
        Called by compile to link all added elements appropriately.
        """
        raise NotImplementedError("Please implement this method")

    def compile(self):
        if any([e is None for e in self.elements]):
            raise AudioAnalyserError("Error: could not create elements.")
        else:
            # Add elements to pipeline.
            pipeline = Gst.Pipeline.new()
            [pipeline.add(e) for e in self.elements]
            self._link_elements()
            return pipeline, self.handlers


class FilterLevelPipeline(BaseVirtualPipeline):
    def __init__(self, source, multichannel, sample_rate, interval,
                 peak_falloff, peak_ttl, handler, on_error, on_eos):
        BaseVirtualPipeline.__init__(self, on_error, on_eos)
        self.__filters = []
        self.handlers.append(('message::element', handler))

        # Audio source.
        self.__audio_source = Gst.ElementFactory.make('pulsesrc', None)
        self.__audio_source.set_property('device', source)
        self.elements.append(self.__audio_source)

        self.__caps = Gst.caps_from_string(
            "audio/x-raw, channels=(int){}, rate=(int){}".format(
                2 if multichannel else 1, sample_rate))
        self.__caps_filter = Gst.ElementFactory.make('audioconvert', None)
        self.elements.append(self.__caps_filter)

        # Level messages.
        self.__level_analyser = Gst.ElementFactory.make('level', None)
        self.__level_analyser.set_property('interval', interval * Gst.MSECOND)
        self.__level_analyser.set_property('peak-falloff', peak_falloff)
        self.__level_analyser.set_property('peak-ttl', peak_ttl * Gst.MSECOND)
        self.elements.append(self.__level_analyser)

        # Sink
        self.__sink = Gst.ElementFactory.make('fakesink', None)
        self.elements.append(self.__sink)

    def __add_filter(self, element):
        self.__filters.append(element)
        self.elements.append(element)

    def _link_elements(self):
        link_ok = self.__audio_source.link(self.__caps_filter)
        if len(self.__filters) == 0:
            link_ok = link_ok and self.__caps_filter.link_filtered(
                self.__level_analyser, self.__caps)
        else:
            # Link to first filter.
            link_ok = link_ok and self.__caps_filter.link_filtered(
                self.__filters[0], self.__caps)

            # Link all filters.
            for i in range(0, len(self.__filters) - 1):
                link_ok = link_ok and self.__filters[i].link(
                    self.__filters[i + 1])

            # Link last filter to level analyser.
            link_ok = link_ok and self.__filters[-1].link(self.__level_analyser)

        link_ok = link_ok and self.__level_analyser.link(self.__sink)

        if not link_ok:
            print("Error: could not link elements.")  # TODO

    def add_limit_filter(self, cutoff, mode='low-pass', poles=4, cheb_type=1):
        audio_filter = Gst.ElementFactory.make('audiocheblimit', None)
        audio_filter.set_property('mode', mode)
        audio_filter.set_property('cutoff', cutoff)
        audio_filter.set_property('poles', poles)
        audio_filter.set_property('type', cheb_type)
        self.__add_filter(audio_filter)

    def add_band_filter(self, lower_cutoff, upper_cutoff, mode='band-pass',
                        poles=4, cheb_type=1):
        audio_filter = Gst.ElementFactory.make('audiochebband', None)
        audio_filter.set_property('mode', mode)
        audio_filter.set_property('lower-frequency', lower_cutoff)
        audio_filter.set_property('upper-frequency', upper_cutoff)
        audio_filter.set_property('poles', poles)
        audio_filter.set_property('type', cheb_type)
        self.__add_filter(audio_filter)


if __name__ == '__main__':
    PULSE_AUDIO_DEVICE = "alsa_output.usb-Propellerhead_Balance_0001002008080-00.analog-stereo.monitor"
    aa = LevelAudioAnalyser(PULSE_AUDIO_DEVICE, print_data,
                            multichannel=False, interval=100)
    aa.start()
    from time import sleep

    while True:
        sleep(1)
