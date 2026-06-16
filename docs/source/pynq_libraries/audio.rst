Audio
=====

The Audio module provides methods to read audio from the input microphone, play
audio to the output speaker, or read and write audio files. The audio module
connects to the audio IP subsystem in overlay to capture and playback data.
The audio module is intended to support different IP subsystems, for example a
line-in, HP/Mic interface using the ADAU1761 codec.


Examples
--------


When an overlay contains an Audio instance named *audio*, it can be accessed
once the overlay is loaded:

.. code-block:: Python

   from pynq.overlays.base import BaseOverlay
   base = BaseOverlay("base.bit")
   pAudio = base.audio
   pAudio.set_volume(20)
   pAudio.load("/home/xilinx/jupyter_notebooks/base/audio/data/recording_0.wav")

   pAudio.play()

More information about the Audio module and the API for reading and writing
audio interfaces, or loading and saving audio files can be found in the
:ref:`pynq-lib-audio` section.
