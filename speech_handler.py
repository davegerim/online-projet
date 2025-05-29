import os
import pyaudio
import wave
import threading
import queue
import time
from openai import OpenAI
from dotenv import load_dotenv

class SpeechHandler:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Queues for audio processing
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        
        # Thread control
        self.is_recording = False
        self.is_playing = False
        self.is_processing = False
        
        # Voice settings
        self.npc_voices = {
            "HR": "alloy",
            "CEO": "echo",
            "CTO": "fable",
            "default": "alloy"
        }

    def start_recording(self):
        """Start recording audio from microphone"""
        self.is_recording = True
        self.record_thread = threading.Thread(target=self._record_audio)
        self.record_thread.start()

    def stop_recording(self):
        """Stop recording audio"""
        self.is_recording = False
        if hasattr(self, 'record_thread'):
            self.record_thread.join()

    def _record_audio(self):
        """Record audio from microphone and put it in the input queue"""
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )

        while self.is_recording:
            data = stream.read(self.CHUNK)
            self.input_queue.put(data)

        stream.stop_stream()
        stream.close()

    def process_audio(self, npc_role="default"):
        """Process audio using OpenAI's Realtime API"""
        self.is_processing = True
        voice = self.npc_voices.get(npc_role, self.npc_voices["default"])
        
        try:
            # Create a real-time stream with OpenAI
            stream = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input="",  # Will be updated in real-time
                response_format="mp3"
            )
            
            # Process audio in real-time
            while self.is_processing:
                if not self.input_queue.empty():
                    audio_data = self.input_queue.get()
                    # Process audio with OpenAI API
                    # Add your real-time processing logic here
                    
        except Exception as e:
            print(f"Error in audio processing: {e}")
        finally:
            self.is_processing = False

    def play_audio(self):
        """Play audio from the output queue"""
        self.is_playing = True
        self.play_thread = threading.Thread(target=self._play_audio)
        self.play_thread.start()

    def stop_playing(self):
        """Stop playing audio"""
        self.is_playing = False
        if hasattr(self, 'play_thread'):
            self.play_thread.join()

    def _play_audio(self):
        """Play audio from the output queue"""
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            output=True,
            frames_per_buffer=self.CHUNK
        )

        while self.is_playing:
            if not self.output_queue.empty():
                data = self.output_queue.get()
                stream.write(data)

        stream.stop_stream()
        stream.close()

    def cleanup(self):
        """Clean up resources"""
        self.stop_recording()
        self.stop_playing()
        self.audio.terminate() 