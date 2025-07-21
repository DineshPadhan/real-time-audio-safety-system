# 🎧 Simple Audio Device Selector with Real-time Processing
# PC Microphone Input → Headphone Output with 70dB Safety Monitoring

import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading
import time
from collections import deque

class SimpleAudioProcessor:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.processing = False
        self.input_stream = None
        self.output_stream = None
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        
        # Safety settings
        self.MAX_DB = 70.0
        
        # Data buffers
        self.input_data = deque(maxlen=self.CHUNK)
        self.output_data = deque(maxlen=self.CHUNK)
        self.db_history = deque(maxlen=200)
        self.max_db_recorded = 0
        
    def get_devices(self):
        """Get and categorize audio devices"""
        input_devices = []
        output_devices = []
        
        for i in range(self.audio.get_device_count()):
            try:
                device_info = self.audio.get_device_info_by_index(i)
                
                # Input devices
                if device_info['maxInputChannels'] > 0:
                    device_type = "🎤 Microphone"
                    if any(keyword in device_info['name'].lower() for keyword in 
                          ['realtek', 'amd audio', 'array', 'pc']):
                        device_type = "🖥️ PC Microphone"
                    elif any(keyword in device_info['name'].lower() for keyword in 
                           ['headset', 'headphone']):
                        device_type = "🎧 Headset Microphone"
                        
                    input_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'type': device_type
                    })
                
                # Output devices
                if device_info['maxOutputChannels'] > 0:
                    device_type = "🔊 Speaker"
                    if any(keyword in device_info['name'].lower() for keyword in 
                          ['headphone', 'headset']):
                        device_type = "🎧 Headphones"
                    elif any(keyword in device_info['name'].lower() for keyword in 
                           ['speaker', 'realtek']):
                        device_type = "🖥️ PC Speakers"
                        
                    output_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'type': device_type
                    })
                    
            except Exception:
                continue
                
        return input_devices, output_devices
    
    def test_headphone_connection(self, device_index):
        """Test if a headphone device is actually connected and functional"""
        try:
            # Try to open the device for output to verify it's actually connected
            test_stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=2,  # Stereo for headphones
                rate=44100,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=1024
            )
            
            # If we can open it, it's connected
            test_stream.close()
            return True
            
        except Exception as e:
            # If we can't open it, it's not properly connected
            return False

    def check_headphone_availability(self, output_devices):
        """Check if headphones are available and warn if not"""
        headphone_devices = [device for device in output_devices if "🎧 Headphones" in device['type']]
        
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
        
        for device in headphone_devices:
            print(f"Testing: {device['name'][:50]}...", end=" ")
            
            if self.test_headphone_connection(device['index']):
                print("✅ CONNECTED")
                connected_headphones.append(device)
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
            for device in connected_headphones:
                print(f"   🎧 {device['name']}")
            print("✅ Ready for safe testing!")
            return True
    
    def select_devices(self):
        """Interactive device selection"""
        input_devices, output_devices = self.get_devices()
        
        # Check for headphones first
        print("\n🎧 HEADPHONE DETECTION")
        print("Checking for connected headphones...")
        
        if not self.check_headphone_availability(output_devices):
            return None, None
        
        print("🎤 AVAILABLE INPUT DEVICES:")
        print("=" * 60)
        for i, device in enumerate(input_devices):
            print(f"  {i}: {device['name'][:50]} - {device['type']}")
        
        print("\\n🔊 AVAILABLE OUTPUT DEVICES:")
        print("=" * 60)
        for i, device in enumerate(output_devices):
            print(f"  {i}: {device['name'][:50]} - {device['type']}")
        
        # Auto-select PC microphone and headphones if available
        selected_input = None
        selected_output = None
        
        # Find PC microphone
        for i, device in enumerate(input_devices):
            if "🖥️ PC Microphone" in device['type']:
                selected_input = device['index']
                print(f"\\n✅ Auto-selected INPUT: {device['name']} - {device['type']}")
                break
        
        # Find headphones
        for i, device in enumerate(output_devices):
            if "🎧 Headphones" in device['type']:
                selected_output = device['index']
                print(f"✅ Auto-selected OUTPUT: {device['name']} - {device['type']}")
                break
        
        # Fallback to manual selection if auto-selection fails
        if selected_input is None:
            try:
                choice = int(input("\\nSelect INPUT device number: "))
                selected_input = input_devices[choice]['index']
                print(f"✅ Selected INPUT: {input_devices[choice]['name']}")
            except:
                print("❌ Invalid selection, using default")
                selected_input = None
        
        if selected_output is None:
            try:
                choice = int(input("\\nSelect OUTPUT device number: "))
                selected_output = output_devices[choice]['index']
                print(f"✅ Selected OUTPUT: {output_devices[choice]['name']}")
            except:
                print("❌ Invalid selection, using default")
                selected_output = None
        
        return selected_input, selected_output
    
    def apply_safety_limiting(self, audio_data):
        """Apply 70dB safety limiting"""
        # Calculate dB level
        rms = np.sqrt(np.mean(audio_data ** 2))
        if rms > 0:
            db_level = 20 * np.log10(rms) + 94  # Calibration
        else:
            db_level = -np.inf
        
        # Track maximum
        if db_level != -np.inf:
            self.max_db_recorded = max(self.max_db_recorded, db_level)
            self.db_history.append(db_level)
        else:
            self.db_history.append(0)
        
        # Apply safety limiting
        if db_level > self.MAX_DB and db_level != -np.inf:
            reduction_db = db_level - self.MAX_DB
            reduction_factor = 10 ** (-reduction_db / 20.0)
            processed = audio_data * reduction_factor
            print(f"🛡️ SAFETY LIMITING: {db_level:.1f} dB → {self.MAX_DB} dB")
        else:
            processed = audio_data.copy()
        
        return processed, db_level
    
    def audio_processing_loop(self, input_device_id, output_device_id):
        """Main audio processing loop"""
        try:
            # Create input stream
            self.input_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                input_device_index=input_device_id,
                frames_per_buffer=self.CHUNK
            )
            
            # Create output stream
            self.output_stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                output=True,
                output_device_index=output_device_id,
                frames_per_buffer=self.CHUNK
            )
            
            print("🎵 Audio streams started successfully!")
            print(f"🛡️ Safety monitoring active - Maximum: {self.MAX_DB} dB")
            
            while self.processing:
                # Read from input
                input_data = self.input_stream.read(self.CHUNK, exception_on_overflow=False)
                audio_input = np.frombuffer(input_data, dtype=np.int16) / 32768.0
                
                # Apply safety processing
                processed_audio, db_level = self.apply_safety_limiting(audio_input)
                
                # Store for visualization
                self.input_data.extend(audio_input)
                self.output_data.extend(processed_audio)
                
                # Send to output
                output_bytes = (processed_audio * 32767).astype(np.int16).tobytes()
                self.output_stream.write(output_bytes)
                
        except Exception as e:
            print(f"❌ Audio processing error: {e}")
        finally:
            self.stop_processing()
    
    def start_processing(self, input_device_id, output_device_id):
        """Start audio processing in a separate thread"""
        self.processing = True
        self.audio_thread = threading.Thread(
            target=self.audio_processing_loop, 
            args=(input_device_id, output_device_id)
        )
        self.audio_thread.daemon = True
        self.audio_thread.start()
    
    def stop_processing(self):
        """Stop audio processing"""
        self.processing = False
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except:
                pass
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass
    
    def create_visualization(self):
        """Create real-time visualization"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('🎧 PC Microphone → Headphone Processing with Safety Monitoring', fontsize=14, fontweight='bold')
        
        # Configure subplots
        ax1.set_title('🎤 Input (PC Microphone)')
        ax1.set_ylim(-1, 1)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylabel('Amplitude')
        
        ax2.set_title('🎧 Output (To Headphones)')
        ax2.set_ylim(-1, 1)
        ax2.grid(True, alpha=0.3)
        ax2.set_ylabel('Amplitude')
        
        ax3.set_title('📊 Frequency Spectrum')
        ax3.set_xlabel('Frequency (Hz)')
        ax3.set_ylabel('Magnitude')
        ax3.set_xlim(0, 8000)
        ax3.grid(True, alpha=0.3)
        
        ax4.set_title('🛡️ Safety Monitor (70 dB Limit)')
        ax4.set_xlabel('Time')
        ax4.set_ylabel('dB Level')
        ax4.axhline(y=70, color='red', linestyle='--', linewidth=2, label='70 dB Safety Limit')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Initialize plot lines
        line_input, = ax1.plot([], [], 'b-', linewidth=1)
        line_output, = ax2.plot([], [], 'g-', linewidth=1)
        line_freq, = ax3.plot([], [], 'r-', linewidth=1)
        line_db, = ax4.plot([], [], 'orange', linewidth=2)
        
        # Status text
        status_text = fig.text(0.02, 0.02, '', fontsize=12, fontweight='bold')
        
        def update_plots(frame):
            if not self.processing:
                return line_input, line_output, line_freq, line_db
            
            # Update input waveform
            if len(self.input_data) >= self.CHUNK:
                input_array = np.array(list(self.input_data)[-self.CHUNK:])
                line_input.set_data(range(len(input_array)), input_array)
                ax1.set_xlim(0, len(input_array))
                
                # Update output waveform
                output_array = np.array(list(self.output_data)[-self.CHUNK:])
                line_output.set_data(range(len(output_array)), output_array)
                ax2.set_xlim(0, len(output_array))
                
                # Update frequency spectrum
                windowed = input_array * np.hanning(len(input_array))
                fft_data = np.fft.fft(windowed)
                magnitude = np.abs(fft_data[:len(fft_data)//2])
                freqs = np.fft.fftfreq(len(fft_data), 1/self.RATE)[:len(fft_data)//2]
                
                line_freq.set_data(freqs, magnitude)
                if magnitude.max() > 0:
                    ax3.set_ylim(0, magnitude.max() * 1.1)
            
            # Update dB monitoring
            if len(self.db_history) > 0:
                db_array = list(self.db_history)
                time_axis = list(range(len(db_array)))
                line_db.set_data(time_axis, db_array)
                ax4.set_xlim(0, max(200, len(db_array)))
                ax4.set_ylim(0, max(80, self.max_db_recorded + 10))
                
                # Update status
                current_db = db_array[-1] if db_array else 0
                if current_db > 70:
                    status_text.set_text(f'⚠️ SAFETY ACTIVE: {current_db:.1f} dB')
                    status_text.set_color('red')
                else:
                    status_text.set_text(f'✅ SAFE: {current_db:.1f} dB | Max: {self.max_db_recorded:.1f} dB')
                    status_text.set_color('green')
            
            return line_input, line_output, line_freq, line_db
        
        # Start animation
        ani = animation.FuncAnimation(fig, update_plots, interval=50, blit=False)
        plt.tight_layout()
        return fig, ani
    
    def run(self):
        """Main execution"""
        print("🎧 PC Microphone → Headphone Audio Processor")
        print("🛡️ 70 dB Safety Monitoring Active")
        print("=" * 60)
        
        # Select devices
        input_device, output_device = self.select_devices()
        
        if input_device is None or output_device is None:
            print("❌ Device selection failed. Exiting for your safety.")
            print("📌 Please connect headphones and restart the application.")
            return
        
        # Start processing
        print("\\n🚀 Starting audio processing...")
        self.start_processing(input_device, output_device)
        
        # Create and show visualization
        print("📊 Opening visualization...")
        fig, ani = self.create_visualization()
        
        try:
            plt.show()
        except KeyboardInterrupt:
            print("\\n⏹️ Stopping...")
        finally:
            self.stop_processing()
            self.audio.terminate()
            print("✅ Audio processing stopped")

if __name__ == "__main__":
    processor = SimpleAudioProcessor()
    processor.run()
