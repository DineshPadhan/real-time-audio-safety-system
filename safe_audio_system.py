#!/usr/bin/env python3
"""
Safe Audio Environment System
Real-time noise cancellation and volume limiting to keep audio below 70 dB
Features:
- Desktop microphone selection
- Real-time noise reduction
- Automatic volume limiting to 70 dB
- Visual monitoring and feedback
"""

import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy import signal
from collections import deque
import threading
import time
import math

class SafeAudioProcessor:
    def __init__(self):
        # Audio parameters
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        # Safety parameters
        self.MAX_DB = 70.0  # Safe dB level
        self.REFERENCE_LEVEL = 20e-6  # Reference for dB calculation (20 µPa)
        
        # Noise reduction parameters
        self.noise_profile = None
        self.noise_learning_duration = 3.0  # seconds to learn noise profile
        self.noise_reduction_factor = 0.7  # How much to reduce noise (0-1)
        
        # Audio processing buffers
        self.input_buffer = deque(maxlen=self.RATE * 5)  # 5 seconds
        self.output_buffer = deque(maxlen=self.RATE * 5)
        self.noise_buffer = deque(maxlen=int(self.RATE * self.noise_learning_duration))
        
        # Processing state
        self.learning_noise = True
        self.noise_learned = False
        self.processing_enabled = True
        
        # PyAudio setup
        self.audio = pyaudio.PyAudio()
        self.input_stream = None
        self.output_stream = None
        
        # Statistics
        self.current_db = 0
        self.max_db_recorded = 0
        
    def list_audio_devices(self):
        """List all available audio input devices with desktop mic detection"""
        print("\n🎤 Available Audio Input Devices:")
        print("-" * 70)
        
        input_devices = []
        desktop_devices = []
        
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                input_devices.append((i, device_info))
                
                print(f"Device {i}: {device_info['name']}")
                print(f"  Max Input Channels: {device_info['maxInputChannels']}")
                print(f"  Default Sample Rate: {device_info['defaultSampleRate']}")
                
                # Identify device type
                name_lower = device_info['name'].lower()
                if any(keyword in name_lower for keyword in 
                      ['desktop', 'built-in', 'internal', 'array', 'motherboard', 'realtek', 'integrated']):
                    print("  🖥️  DESKTOP MICROPHONE (Recommended)")
                    desktop_devices.append((i, device_info))
                elif any(keyword in name_lower for keyword in 
                        ['headset', 'headphone', 'usb headset', 'bluetooth']):
                    print("  🎧  HEADPHONE/HEADSET MICROPHONE")
                elif 'usb' in name_lower:
                    print("  🔌  USB MICROPHONE")
                else:
                    print("  🎤  MICROPHONE")
                print()
                
        return input_devices, desktop_devices
    
    def list_audio_output_devices(self):
        """List all available audio output devices with headphone detection"""
        print("\n🎧 Available Audio Output Devices:")
        print("-" * 70)
        
        output_devices = []
        headphone_devices = []
        
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxOutputChannels'] > 0:
                output_devices.append((i, device_info))
                
                print(f"Device {i}: {device_info['name']}")
                print(f"  Max Output Channels: {device_info['maxOutputChannels']}")
                print(f"  Default Sample Rate: {device_info['defaultSampleRate']}")
                
                # Identify device type
                name_lower = device_info['name'].lower()
                if any(keyword in name_lower for keyword in 
                      ['headphone', 'headset', 'usb headset', 'bluetooth', 'earphone', 'airpods', 'buds']):
                    print("  🎧  HEADPHONE/HEADSET (Recommended for testing)")
                    headphone_devices.append((i, device_info))
                elif any(keyword in name_lower for keyword in 
                        ['speaker', 'built-in', 'internal', 'realtek', 'integrated']):
                    print("  🔊  SPEAKER (Not recommended for testing)")
                elif 'usb' in name_lower:
                    print("  🔌  USB AUDIO DEVICE")
                else:
                    print("  📢  AUDIO OUTPUT")
                print()
                
        return output_devices, headphone_devices
    
    def test_headphone_connection(self, device_id):
        """Test if a headphone device is actually connected and functional"""
        try:
            # Try to open the device for output to verify it's actually connected
            test_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=2,  # Stereo for headphones
                rate=44100,
                output=True,
                output_device_index=device_id,
                frames_per_buffer=1024
            )
            
            # If we can open it, it's connected
            test_stream.close()
            return True
            
        except Exception as e:
            # If we can't open it, it's not properly connected
            return False
    
    def check_headphone_connection(self):
        """Check if headphones are connected and show warning if not"""
        output_devices, headphone_devices = self.list_audio_output_devices()
        
        # First check if any headphone devices are listed
        if not headphone_devices:
            print("\n" + "⚠️ " * 20)
            print("⚠️  WARNING: NO HEADPHONES DETECTED! ⚠️")
            print("⚠️ " * 20)
            print("\n🎧 HEADPHONES ARE MANDATORY FOR PROPER TESTING!")
            print("\nReasons why headphones are required:")
            print("✓ Prevents audio feedback loops")
            print("✓ Ensures accurate noise cancellation testing")
            print("✓ Protects your hearing with controlled output")
            print("✓ Avoids interference with microphone input")
            print("✓ Provides isolated listening environment")
            print("\n📌 Please connect headphones and restart the application.")
            print("   Supported: Wired, Wireless, USB, Bluetooth headphones")
            print("\n" + "⚠️ " * 20)
            
            while True:
                choice = input("\nDo you want to continue anyway? (y/N): ").strip().lower()
                if choice in ['n', 'no', '']:
                    print("✅ Good choice! Please connect headphones and restart.")
                    return False
                elif choice in ['y', 'yes']:
                    print("⚠️  Proceeding without headphones - testing may not be accurate!")
                    print("⚠️  Please use low volume to avoid feedback!")
                    return True
                else:
                    print("Please enter 'y' for yes or 'n' for no")
        
        # Now test if the detected headphones are actually connected
        print("\n🔍 Testing headphone connections...")
        connected_headphones = []
        
        for device_id, device_info in headphone_devices:
            print(f"Testing: {device_info['name'][:50]}...", end=" ")
            
            if self.test_headphone_connection(device_id):
                print("✅ CONNECTED")
                connected_headphones.append((device_id, device_info))
            else:
                print("❌ NOT CONNECTED")
        
        if not connected_headphones:
            print("\n" + "⚠️ " * 20)
            print("⚠️  WARNING: HEADPHONES FOUND BUT NOT CONNECTED! ⚠️")
            print("⚠️ " * 20)
            print(f"\n🎧 Found {len(headphone_devices)} headphone device(s) but NONE are properly connected!")
            print("\nPossible issues:")
            print("❌ Headphones are unplugged")
            print("❌ Bluetooth headphones are not paired/connected")
            print("❌ USB headphones have driver issues")
            print("❌ Audio drivers need to be updated")
            print("❌ Headphones are connected to wrong audio jack")
            
            print("\n🔧 Try these solutions:")
            print("1. Ensure headphones are fully plugged in")
            print("2. Check Bluetooth connection status")
            print("3. Try different USB port for USB headphones")
            print("4. Update audio drivers")
            print("5. Test headphones in Windows Sound settings")
            print("\n📌 Please properly connect headphones and restart the application.")
            print("\n" + "⚠️ " * 20)
            
            while True:
                choice = input("\nDo you want to continue anyway? (y/N): ").strip().lower()
                if choice in ['n', 'no', '']:
                    print("✅ Good choice! Please properly connect headphones and restart.")
                    return False
                elif choice in ['y', 'yes']:
                    print("⚠️  Proceeding without properly connected headphones!")
                    print("⚠️  Audio may not work correctly and feedback is possible!")
                    return True
                else:
                    print("Please enter 'y' for yes or 'n' for no")
        else:
            print(f"\n✅ Headphones properly connected! Found {len(connected_headphones)} working headphone device(s):")
            for device_id, device_info in connected_headphones:
                print(f"   🎧 Device {device_id}: {device_info['name']}")
            print("✅ Ready for safe testing!")
            return True
        
    def select_desktop_microphone(self):
        """Allow user to select the desktop microphone"""
        input_devices, desktop_devices = self.list_audio_devices()
        
        if not input_devices:
            print("❌ No input devices found!")
            return None
            
        # Suggest desktop microphones
        if desktop_devices:
            print(f"🖥️  Auto-detected {len(desktop_devices)} desktop microphone(s):")
            for device_id, device_info in desktop_devices:
                print(f"  Device {device_id}: {device_info['name']}")
            print()
            
        while True:
            try:
                print("Selection options:")
                print("  • Enter device number (0-{})".format(len(input_devices)-1))
                print("  • Type 'auto' to use first desktop microphone")
                print("  • Type 'list' to see devices again")
                
                choice = input("\nEnter your choice: ").strip().lower()
                
                if choice == 'auto':
                    if desktop_devices:
                        device_id = desktop_devices[0][0]
                        device_info = desktop_devices[0][1]
                        print(f"✅ Auto-selected desktop microphone: {device_info['name']}")
                        return device_id
                    else:
                        print("❌ No desktop microphones detected. Please select manually.")
                        continue
                        
                elif choice == 'list':
                    self.list_audio_devices()
                    continue
                    
                else:
                    device_id = int(choice)
                    # Find the device info
                    device_info = None
                    for id, info in input_devices:
                        if id == device_id:
                            device_info = info
                            break
                            
                    if device_info:
                        print(f"✅ Selected: {device_info['name']}")
                        return device_id
                    else:
                        print("❌ Invalid device number")
                        
            except ValueError:
                print("❌ Please enter a valid number, 'auto', or 'list'")
            except KeyboardInterrupt:
                print("\n❌ Selection cancelled")
                return None
        self.max_db_recorded = 0
        self.processed_db = 0
        
    def db_to_linear(self, db):
        """Convert dB to linear scale"""
        return 10 ** (db / 20.0)
        
    def linear_to_db(self, linear):
        """Convert linear amplitude to dB"""
        if linear <= 0:
            return -np.inf
        return 20 * np.log10(abs(linear) + 1e-10)
        
    def calculate_db_level(self, audio_data):
        """Calculate dB level of audio data"""
        if len(audio_data) == 0:
            return -np.inf
            
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        # Convert to dB relative to full scale
        if rms > 0:
            db_level = 20 * np.log10(rms)
            # Adjust to approximate real-world dB levels
            # This is a rough calibration - in practice you'd calibrate with a sound meter
            return db_level + 94  # Rough calibration offset
        return -np.inf
        
    def spectral_subtraction(self, audio_data, noise_spectrum):
        """Apply spectral subtraction for noise reduction"""
        if noise_spectrum is None or len(audio_data) < 64:
            return audio_data
            
        # Apply window
        windowed_audio = audio_data * np.hanning(len(audio_data))
        
        # FFT
        audio_fft = np.fft.fft(windowed_audio)
        audio_spectrum = np.abs(audio_fft)
        audio_phase = np.angle(audio_fft)
        
        # Spectral subtraction
        enhanced_spectrum = np.maximum(
            audio_spectrum - self.noise_reduction_factor * noise_spectrum,
            0.1 * audio_spectrum  # Floor to prevent over-subtraction
        )
        
        # Reconstruct signal
        enhanced_fft = enhanced_spectrum * np.exp(1j * audio_phase)
        enhanced_audio = np.real(np.fft.ifft(enhanced_fft))
        
        return enhanced_audio
        
    def adaptive_volume_control(self, audio_data):
        """Adaptive volume control to keep below 70 dB"""
        current_db = self.calculate_db_level(audio_data)
        
        if current_db > self.MAX_DB:
            # Calculate reduction factor needed
            reduction_db = current_db - self.MAX_DB
            reduction_factor = self.db_to_linear(-reduction_db)
            
            # Apply smooth reduction to avoid clicks
            audio_data = audio_data * reduction_factor
            
            # Apply soft limiting
            audio_data = np.tanh(audio_data * 0.8) * 0.8
            
        return audio_data, current_db
        
    def low_pass_filter(self, audio_data, cutoff_freq=8000):
        """Apply low-pass filter to reduce high-frequency noise"""
        nyquist = self.RATE / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        # Design filter
        b, a = signal.butter(4, normalized_cutoff, btype='low')
        
        # Apply filter
        filtered_audio = signal.filtfilt(b, a, audio_data)
        return filtered_audio
        
    def process_audio_chunk(self, audio_data):
        """Process a chunk of audio data"""
        # Convert to float
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        # Store original input level
        input_db = self.calculate_db_level(audio_float)
        self.current_db = input_db
        self.max_db_recorded = max(self.max_db_recorded, input_db)
        
        if self.learning_noise:
            # Learn noise profile
            self.noise_buffer.extend(audio_float)
            
            if len(self.noise_buffer) >= int(self.RATE * self.noise_learning_duration):
                # Calculate noise spectrum
                noise_array = np.array(list(self.noise_buffer))
                windowed_noise = noise_array * np.hanning(len(noise_array))
                noise_fft = np.fft.fft(windowed_noise)
                self.noise_profile = np.abs(noise_fft)
                
                self.learning_noise = False
                self.noise_learned = True
                print("✅ Noise profile learned! Starting active noise reduction...")
                
            return audio_data  # Return original during learning
            
        if not self.processing_enabled:
            return audio_data
            
        # Apply noise reduction
        if self.noise_learned and len(audio_float) > 0:
            # Spectral subtraction
            if len(audio_float) == len(self.noise_profile):
                audio_float = self.spectral_subtraction(audio_float, self.noise_profile)
            
            # Low-pass filtering for additional noise reduction
            audio_float = self.low_pass_filter(audio_float)
            
            # Adaptive volume control
            audio_float, processed_db = self.adaptive_volume_control(audio_float)
            self.processed_db = processed_db
            
        # Convert back to int16
        audio_int = np.clip(audio_float * 32768.0, -32768, 32767).astype(np.int16)
        
        return audio_int
        
    def audio_callback(self, in_data, frame_count, time_info, status):
        """Audio input callback - input only mode"""
        # Convert input data
        input_audio = np.frombuffer(in_data, dtype=np.int16)
        
        # Process audio (for monitoring and safety)
        processed_audio = self.process_audio_chunk(input_audio)
        
        # Store for visualization
        self.input_buffer.extend(input_audio)
        self.output_buffer.extend(processed_audio)
        
        # Return only continue flag (no audio output to avoid device conflicts)
        return (None, pyaudio.paContinue)
        
    def start_processing(self, input_device_id=None):
        """Start real-time audio processing with specified microphone"""
        try:
            # Input stream (microphone)
            self.input_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                # Removed output=True to avoid device combination conflicts
                input_device_index=input_device_id,  # Use selected microphone
                frames_per_buffer=self.CHUNK,
                stream_callback=self.audio_callback
            )
            
            if input_device_id is not None:
                device_info = self.audio.get_device_info_by_index(input_device_id)
                print(f"🎤 Using microphone: {device_info['name']}")
            else:
                print("🎤 Using default microphone")
                
            print("🔊 Real-time audio processing started!")
            print(f"�️ Target maximum level: {self.MAX_DB} dB")
            print("📊 Learning noise profile for 3 seconds...")
            print("   Please be quiet or speak at normal levels...")
            
        except Exception as e:
            print(f"❌ Error starting audio processing: {e}")
            
            # Try with different audio parameters
            print("� Trying alternative audio configuration...")
            try:
                # Try with different format and settings
                self.input_stream = self.audio.open(
                    format=pyaudio.paFloat32,  # Try float32 instead
                    channels=1,  # Force mono
                    rate=44100,  # Standard rate
                    input=True,
                    input_device_index=input_device_id,
                    frames_per_buffer=512,  # Smaller buffer
                    stream_callback=self.audio_callback
                )
                
                # Update our settings to match
                self.FORMAT = pyaudio.paFloat32
                self.CHANNELS = 1
                self.RATE = 44100
                self.CHUNK = 512
                
                print("✅ Alternative audio configuration successful!")
                if input_device_id is not None:
                    device_info = self.audio.get_device_info_by_index(input_device_id)
                    print(f"🎤 Using microphone: {device_info['name']}")
                print("🔊 Real-time audio processing started!")
                print(f"🛡️ Target maximum level: {self.MAX_DB} dB")
                print("📊 Learning noise profile for 3 seconds...")
                
            except Exception as e2:
                print(f"❌ Alternative configuration also failed: {e2}")
                print("💡 Troubleshooting:")
                print("   • Check microphone and speaker connections")
                print("   • Ensure audio permissions are granted")
                print("   • Try selecting a different microphone")
                print("   • Run as administrator if needed")
                print("   • Close other audio applications")
                raise
            
    def stop_processing(self):
        """Stop audio processing"""
        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            
        self.audio.terminate()
        print("🛑 Audio processing stopped")
        
    def get_visualization_data(self):
        """Get data for visualization"""
        input_data = np.array(list(self.input_buffer)[-self.CHUNK*4:]) if self.input_buffer else np.array([])
        output_data = np.array(list(self.output_buffer)[-self.CHUNK*4:]) if self.output_buffer else np.array([])
        
        return input_data, output_data
        
    def visualize(self):
        """Create real-time visualization"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('🔇 Safe Audio Environment System - Real-time Noise Reduction', fontsize=16)
        
        # Input waveform
        ax1.set_title('🎤 Input Audio (Raw)')
        ax1.set_ylabel('Amplitude')
        ax1.grid(True, alpha=0.3)
        line1, = ax1.plot([], [], 'b-', linewidth=1, label='Input')
        ax1.legend()
        
        # Output waveform
        ax2.set_title('🔊 Output Audio (Processed)')
        ax2.set_ylabel('Amplitude')
        ax2.grid(True, alpha=0.3)
        line2, = ax2.plot([], [], 'g-', linewidth=1, label='Output')
        ax2.legend()
        
        # dB levels
        ax3.set_title('📊 Audio Levels (dB)')
        ax3.set_ylabel('dB Level')
        ax3.set_ylim(0, 100)
        ax3.grid(True, alpha=0.3)
        ax3.axhline(y=self.MAX_DB, color='r', linestyle='--', linewidth=2, label='70 dB Limit')
        
        # Create bars for dB display
        bars = ax3.bar(['Input dB', 'Output dB', 'Max Recorded'], [0, 0, 0], 
                      color=['red', 'green', 'orange'], alpha=0.7)
        ax3.legend()
        
        # Processing status
        ax4.set_title('🔧 System Status')
        ax4.set_xlim(0, 10)
        ax4.set_ylim(0, 10)
        ax4.axis('off')
        
        status_text = ax4.text(5, 8, '', fontsize=12, ha='center', va='top',
                              bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        def animate(frame):
            # Get audio data
            input_data, output_data = self.get_visualization_data()
            
            # Update waveforms
            if len(input_data) > 0:
                time_axis = np.arange(len(input_data))
                line1.set_data(time_axis, input_data)
                ax1.set_xlim(0, len(input_data))
                ax1.set_ylim(-32768, 32767)
                
            if len(output_data) > 0:
                time_axis = np.arange(len(output_data))
                line2.set_data(time_axis, output_data)
                ax2.set_xlim(0, len(output_data))
                ax2.set_ylim(-32768, 32767)
                
            # Update dB levels
            current_input_db = max(0, self.current_db) if self.current_db > -np.inf else 0
            current_output_db = max(0, self.processed_db) if hasattr(self, 'processed_db') and self.processed_db > -np.inf else 0
            max_recorded_db = max(0, self.max_db_recorded) if self.max_db_recorded > -np.inf else 0
            
            bars[0].set_height(min(current_input_db, 100))
            bars[1].set_height(min(current_output_db, 100))
            bars[2].set_height(min(max_recorded_db, 100))
            
            # Color coding for safety
            bars[0].set_color('red' if current_input_db > self.MAX_DB else 'orange' if current_input_db > 60 else 'green')
            bars[1].set_color('red' if current_output_db > self.MAX_DB else 'green')
            
            # Update status
            if self.learning_noise:
                status = "🔍 Learning Noise Profile..."
                remaining = max(0, self.noise_learning_duration - len(self.noise_buffer) / self.RATE)
                status += f"\nTime remaining: {remaining:.1f}s"
            elif self.noise_learned:
                status = "✅ Active Noise Reduction\n🔊 Audio Processing ON"
                if current_output_db > self.MAX_DB:
                    status += "\n⚠️ WARNING: Still above 70dB!"
                else:
                    status += "\n✅ Safe level maintained"
            else:
                status = "⏸️ Processing Paused"
                
            status += f"\n\nInput: {current_input_db:.1f} dB"
            status += f"\nOutput: {current_output_db:.1f} dB"
            status += f"\nReduction: {current_input_db - current_output_db:.1f} dB"
            
            status_text.set_text(status)
            
            return line1, line2, status_text
            
        # Start processing
        self.start_processing()
        
        # Animation
        ani = animation.FuncAnimation(fig, animate, interval=50, blit=False)
        
        plt.tight_layout()
        
        print("\n" + "="*60)
        print("🔇 SAFE AUDIO ENVIRONMENT SYSTEM ACTIVE")
        print("="*60)
        print("📊 This system will:")
        print("   • Learn your environment's noise profile")
        print("   • Apply real-time noise reduction")
        print("   • Keep audio levels below 70 dB for safety")
        print("   • Process audio in real-time")
        print()
        print("🎤 Speak normally - the system will adapt!")
        print("💡 Close the window to stop processing")
        print("="*60)
        
        plt.show()
        
        return ani

def main():
    """Main function"""
    print("�️ Safe Audio Environment System")
    print("Protecting your hearing by keeping audio below 70 dB")
    print("Specifically designed to use desktop microphones")
    print("="*60)
    
    processor = None
    
    try:
        processor = SafeAudioProcessor()
        
        # Check headphone connection first
        print("\n🎧 HEADPHONE DETECTION")
        print("Checking for connected headphones...")
        
        if not processor.check_headphone_connection():
            print("❌ Headphone check failed. Exiting for your safety.")
            return
        
        # Select desktop microphone
        print("\n🎤 MICROPHONE SELECTION")
        print("For best results, please select your desktop microphone")
        print("(not headphone microphone)")
        
        selected_device = processor.select_desktop_microphone()
        
        if selected_device is None:
            print("❌ No microphone selected. Exiting.")
            return
            
        # Start processing with selected device
        processor.start_processing(input_device_id=selected_device)
        
        # Start visualization
        ani = processor.visualize()
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   • Check microphone and headphone connections")
        print("   • Ensure headphones are properly connected")
        print("   • Ensure audio permissions are granted")
        print("   • Try selecting a different microphone")
        print("   • Run as administrator if needed")
        print("   • Close other audio applications")
    finally:
        if processor:
            processor.stop_processing()

if __name__ == "__main__":
    main()
