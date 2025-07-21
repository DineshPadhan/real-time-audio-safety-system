#!/usr/bin/env python3
"""
Ultimate Audio Visualizer
- Play audio files with visualization
- Live microphone visualization
- Real-time frequency analysis
"""

import sys
import os
from pydub import AudioSegment
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import threading
import time
import pygame

class UltimateAudioVisualizer:
    def __init__(self):
        self.mode = None  # 'file' or 'mic'
        self.running = False
        
    def test_headphone_connection(self, audio, device_id):
        """Test if a headphone device is actually connected and functional"""
        try:
            # Try to open the device for output to verify it's actually connected
            test_stream = audio.open(
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
    
    def check_headphones(self):
        """Advanced check for headphone availability and connection"""
        try:
            import pyaudio
            audio = pyaudio.PyAudio()
            
            # First, find all potential headphone devices
            headphone_devices = []
            for i in range(audio.get_device_count()):
                try:
                    device_info = audio.get_device_info_by_index(i)
                    if device_info['maxOutputChannels'] > 0:
                        name_lower = device_info['name'].lower()
                        if any(keyword in name_lower for keyword in 
                              ['headphone', 'headset', 'earphone', 'airpods', 'buds']):
                            headphone_devices.append((i, device_info))
                except:
                    continue
            
            if not headphone_devices:
                print("\n" + "⚠️ " * 20)
                print("⚠️  WARNING: NO HEADPHONES DETECTED! ⚠️")
                print("⚠️ " * 20)
                print("\n🎧 HEADPHONES ARE RECOMMENDED FOR OPTIMAL EXPERIENCE!")
                print("\nBenefits of using headphones:")
                print("✓ Better audio quality and isolation")
                print("✓ Prevents audio feedback in microphone mode")
                print("✓ Enhanced visualization accuracy")
                print("✓ Personal listening experience")
                print("\n📌 Consider connecting headphones for the best experience.")
                print("\n" + "⚠️ " * 20)
                
                choice = input("\nContinue anyway? (y/N): ").strip().lower()
                audio.terminate()
                if choice not in ['y', 'yes']:
                    return False
                return True
            
            # Now test if the detected headphones are actually connected
            print("\n🔍 Testing headphone connections...")
            connected_headphones = []
            
            for device_id, device_info in headphone_devices:
                print(f"Testing: {device_info['name'][:50]}...", end=" ")
                
                if self.test_headphone_connection(audio, device_id):
                    print("✅ CONNECTED")
                    connected_headphones.append((device_id, device_info))
                else:
                    print("❌ NOT CONNECTED")
            
            audio.terminate()
            
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
                print("\n📌 Consider properly connecting headphones for the best experience.")
                print("\n" + "⚠️ " * 20)
                
                choice = input("\nContinue anyway? (y/N): ").strip().lower()
                if choice not in ['y', 'yes']:
                    return False
                print("⚠️  Proceeding without properly connected headphones!")
                return True
            else:
                print(f"\n✅ Headphones properly connected! Found {len(connected_headphones)} working headphone device(s):")
                for device_id, device_info in connected_headphones:
                    print(f"   🎧 Device {device_id}: {device_info['name']}")
                print("✅ Ready for optimal experience!")
                return True
                
        except Exception:
            # If detection fails, continue anyway
            return True
    
    def visualize_audio_file(self, audio_file):
        """Visualize audio file playback"""
        print(f"🎵 Loading audio file: {audio_file}")
        
        # Load audio
        if audio_file.lower().endswith('.wav'):
            audio = AudioSegment.from_wav(audio_file)
        elif audio_file.lower().endswith('.mp3'):
            audio = AudioSegment.from_mp3(audio_file)
        else:
            audio = AudioSegment.from_file(audio_file)
            
        # Convert to numpy array
        audio_data = np.array(audio.get_array_of_samples())
        if audio.channels == 2:
            audio_data = audio_data.reshape((-1, 2))
            audio_data = audio_data[:, 0]  # Take left channel
            
        sample_rate = audio.frame_rate
        duration = len(audio) / 1000.0
        
        # Initialize pygame for playback
        pygame.mixer.init()
        temp_file = "temp_playback.wav"
        audio.export(temp_file, format="wav")
        
        # Create visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        fig.suptitle(f'Audio File Visualization: {os.path.basename(audio_file)}', fontsize=16)
        
        # Full waveform
        time_axis = np.linspace(0, duration, len(audio_data))
        ax1.plot(time_axis, audio_data, color='steelblue', linewidth=0.5, alpha=0.7)
        ax1.set_title('Full Waveform')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Amplitude')
        ax1.grid(True, alpha=0.3)
        
        # Position indicator
        position_line = ax1.axvline(x=0, color='red', linewidth=2, label='Current Position')
        ax1.legend()
        
        # Real-time window
        ax2.set_title('Real-time Window (2 seconds)')
        ax2.set_xlabel('Time (seconds)')
        ax2.set_ylabel('Amplitude')
        ax2.grid(True, alpha=0.3)
        line, = ax2.plot([], [], color='limegreen', linewidth=2)
        
        # Playback control
        playing = False
        start_time = 0
        
        def start_playback():
            nonlocal playing, start_time
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            playing = True
            start_time = time.time()
            print(f"Playing: {audio_file}")
            
        def get_position():
            if playing and pygame.mixer.music.get_busy():
                return time.time() - start_time
            return 0
            
        def animate(frame):
            current_pos = get_position()
            
            # Update position line
            position_line.set_xdata([current_pos, current_pos])
            
            # Update real-time window
            window_duration = 2.0
            start_sample = int(current_pos * sample_rate)
            end_sample = int((current_pos + window_duration) * sample_rate)
            
            if start_sample < len(audio_data) and playing:
                end_sample = min(end_sample, len(audio_data))
                window_data = audio_data[start_sample:end_sample]
                
                if len(window_data) > 0:
                    window_time = np.linspace(current_pos, 
                                            current_pos + len(window_data)/sample_rate, 
                                            len(window_data))
                    line.set_data(window_time, window_data)
                    ax2.set_xlim(current_pos, current_pos + window_duration)
                    
                    y_max = max(abs(np.max(window_data)), abs(np.min(window_data)))
                    if y_max > 0:
                        ax2.set_ylim(-y_max * 1.1, y_max * 1.1)
                        
            ax2.set_title(f'Real-time Window - {current_pos:.1f}s / {duration:.1f}s')
            return position_line, line
            
        # Start playback
        audio_thread = threading.Thread(target=start_playback)
        audio_thread.daemon = True
        audio_thread.start()
        
        # Animation
        ani = animation.FuncAnimation(fig, animate, interval=50, blit=False)
        plt.tight_layout()
        plt.show()
        
        # Cleanup
        pygame.mixer.music.stop()
        if os.path.exists(temp_file):
            os.remove(temp_file)
            
    def visualize_microphone(self):
        """Real-time microphone visualization with device selection"""
        print("🎤 Starting microphone visualization with device selection...")
        
        # Initialize PyAudio for device detection
        p = pyaudio.PyAudio()
        
        # Get available devices
        input_devices = []
        output_devices = []
        
        for i in range(p.get_device_count()):
            try:
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:
                    input_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels']
                    })
                if device_info['maxOutputChannels'] > 0:
                    output_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxOutputChannels']
                    })
            except:
                continue
        
        # Audio settings
        CHUNK = 1024 * 2
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        # Create visualization with device selection
        fig = plt.figure(figsize=(14, 10))
        
        # Create grid layout
        gs = fig.add_gridspec(4, 2, height_ratios=[0.8, 1, 1, 1], hspace=0.3, wspace=0.3)
        
        # Device selection area
        ax_controls = fig.add_subplot(gs[0, :])
        ax_controls.axis('off')
        ax_controls.text(0.5, 0.8, '🎧 Audio Device Selection & Real-time Processing', 
                        ha='center', va='center', fontsize=16, fontweight='bold',
                        transform=ax_controls.transAxes)
        
        # Audio plots
        ax1 = fig.add_subplot(gs[1, 0])  # Input waveform
        ax2 = fig.add_subplot(gs[1, 1])  # Output waveform
        ax3 = fig.add_subplot(gs[2, :])  # Frequency spectrum
        ax4 = fig.add_subplot(gs[3, :])  # dB monitoring
        
        # Configure plots
        ax1.set_title('🎤 Input (Microphone)')
        ax1.set_xlabel('Sample')
        ax1.set_ylabel('Amplitude')
        ax1.set_ylim(-1, 1)
        ax1.set_xlim(0, CHUNK)
        ax1.grid(True, alpha=0.3)
        
        ax2.set_title('🔊 Output (Processed)')
        ax2.set_xlabel('Sample')
        ax2.set_ylabel('Amplitude')
        ax2.set_ylim(-1, 1)
        ax2.set_xlim(0, CHUNK)
        ax2.grid(True, alpha=0.3)
        
        ax3.set_title('📊 Frequency Spectrum')
        ax3.set_xlabel('Frequency (Hz)')
        ax3.set_ylabel('Magnitude')
        ax3.set_xlim(0, RATE // 2)
        ax3.grid(True, alpha=0.3)
        
        ax4.set_title('🛡️ Safety Monitor (70 dB Limit)')
        ax4.set_xlabel('Time (frames)')
        ax4.set_ylabel('dB Level')
        ax4.axhline(y=70, color='red', linestyle='--', linewidth=2, label='70 dB Safety Limit')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Initialize plot lines
        line_input, = ax1.plot(np.arange(CHUNK), np.zeros(CHUNK), 'b-', linewidth=1)
        line_output, = ax2.plot(np.arange(CHUNK), np.zeros(CHUNK), 'g-', linewidth=1)
        line_freq, = ax3.plot(np.arange(CHUNK // 2), np.zeros(CHUNK // 2), 'r-', linewidth=1)
        line_db, = ax4.plot([], [], 'orange', linewidth=2)
        
        # Device selection variables
        self.selected_input_device = None
        self.selected_output_device = None
        self.stream_input = None
        self.stream_output = None
        self.processing_active = False
        
        # Safety monitoring
        self.db_history = []
        self.max_db_recorded = 0
        
        # Auto-select devices (PC mic + headphones)
        def auto_select_devices():
            """Auto-select PC microphone and headphones"""
            # Find PC microphone
            for device in input_devices:
                if any(x in device['name'].lower() for x in ['realtek', 'amd', 'array', 'pc']):
                    self.selected_input_device = device['index']
                    ax_controls.text(0.25, 0.4, f"🎤 Input: {device['name'][:30]}...", 
                                   ha='center', va='center', fontsize=10,
                                   transform=ax_controls.transAxes, 
                                   bbox=dict(boxstyle='round', facecolor='lightblue'))
                    print(f"✅ Auto-selected input: {device['name']}")
                    break
            
            # Find headphones
            for device in output_devices:
                if any(x in device['name'].lower() for x in ['headphone', 'headset']):
                    self.selected_output_device = device['index']
                    ax_controls.text(0.75, 0.4, f"🔊 Output: {device['name'][:30]}...", 
                                   ha='center', va='center', fontsize=10,
                                   transform=ax_controls.transAxes,
                                   bbox=dict(boxstyle='round', facecolor='lightgreen'))
                    print(f"✅ Auto-selected output: {device['name']}")
                    break
            
            fig.canvas.draw()
        
        # Device selection buttons
        def on_select_input_device(event):
            """Cycle through input devices"""
            if not input_devices:
                print("❌ No input devices found!")
                return
            
            # Find current device index
            current_idx = 0
            if self.selected_input_device:
                for i, device in enumerate(input_devices):
                    if device['index'] == self.selected_input_device:
                        current_idx = i
                        break
            
            # Move to next device
            next_idx = (current_idx + 1) % len(input_devices)
            device = input_devices[next_idx]
            self.selected_input_device = device['index']
            
            device_type = "🖥️ PC MIC" if any(x in device['name'].lower() for x in ['realtek', 'amd', 'array']) else "🎧 HEADSET"
            ax_controls.text(0.25, 0.4, f"🎤 {device['name'][:25]}... - {device_type}", 
                           ha='center', va='center', fontsize=9,
                           transform=ax_controls.transAxes, 
                           bbox=dict(boxstyle='round', facecolor='lightblue'))
            print(f"✅ Selected input: {device['name']} - {device_type}")
            fig.canvas.draw()
        
        def on_select_output_device(event):
            """Cycle through output devices"""
            if not output_devices:
                print("❌ No output devices found!")
                return
            
            # Find current device index
            current_idx = 0
            if self.selected_output_device:
                for i, device in enumerate(output_devices):
                    if device['index'] == self.selected_output_device:
                        current_idx = i
                        break
            
            # Move to next device
            next_idx = (current_idx + 1) % len(output_devices)
            device = output_devices[next_idx]
            self.selected_output_device = device['index']
            
            device_type = "🎧 HEADPHONES" if any(x in device['name'].lower() for x in ['headset', 'headphone']) else "🖥️ SPEAKERS"
            ax_controls.text(0.75, 0.4, f"🔊 {device['name'][:25]}... - {device_type}", 
                           ha='center', va='center', fontsize=9,
                           transform=ax_controls.transAxes,
                           bbox=dict(boxstyle='round', facecolor='lightgreen'))
            print(f"✅ Selected output: {device['name']} - {device_type}")
            fig.canvas.draw()
        
        def on_start_processing(event):
            """Start audio processing with separate streams"""
            # Auto-select if no devices selected
            if self.selected_input_device is None or self.selected_output_device is None:
                print("🔄 Auto-selecting devices...")
                auto_select_devices()
            
            if self.selected_input_device is None or self.selected_output_device is None:
                print("❌ Could not find suitable devices! Please select manually.")
                return
            
            try:
                # Start input stream only first
                self.stream_input = p.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=self.selected_input_device,
                    frames_per_buffer=CHUNK
                )
                
                print("✅ Input stream started!")
                
                # Try to start output stream separately
                try:
                    self.stream_output = p.open(
                        format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        output_device_index=self.selected_output_device,
                        frames_per_buffer=CHUNK
                    )
                    print("✅ Output stream started!")
                    
                except Exception as output_error:
                    print(f"⚠️ Output stream failed: {output_error}")
                    print("📊 Continuing with input-only mode (monitoring only)")
                    self.stream_output = None
                
                self.processing_active = True
                print("✅ Audio processing started!")
                
                status_text = "🟢 PROCESSING ACTIVE"
                if self.stream_output is None:
                    status_text += " (Monitor Only)"
                else:
                    status_text += " (Full I/O)"
                
                ax_controls.text(0.5, 0.1, status_text, 
                               ha='center', va='center', fontsize=11, fontweight='bold',
                               transform=ax_controls.transAxes,
                               bbox=dict(boxstyle='round', facecolor='lightgreen'))
                fig.canvas.draw()
                
            except Exception as e:
                print(f"❌ Failed to start input stream: {e}")
                print("💡 Try:")
                print("   • Close other audio applications")
                print("   • Select different devices")
                print("   • Run as administrator")
                self.processing_active = False
        
        def on_stop_processing(event):
            """Stop audio processing"""
            self.processing_active = False
            if self.stream_input:
                self.stream_input.stop_stream()
                self.stream_input.close()
            if self.stream_output:
                self.stream_output.stop_stream()
                self.stream_output.close()
            print("⏹️ Audio processing stopped")
            ax_controls.text(0.5, 0.1, "🔴 STOPPED", 
                           ha='center', va='center', fontsize=12, fontweight='bold',
                           transform=ax_controls.transAxes,
                           bbox=dict(boxstyle='round', facecolor='lightcoral'))
            fig.canvas.draw()
        
        # Add control buttons using matplotlib widgets
        from matplotlib.widgets import Button
        
        # Button positions
        ax_btn1 = plt.axes([0.1, 0.02, 0.15, 0.04])
        ax_btn2 = plt.axes([0.3, 0.02, 0.15, 0.04]) 
        ax_btn3 = plt.axes([0.5, 0.02, 0.15, 0.04])
        ax_btn4 = plt.axes([0.7, 0.02, 0.15, 0.04])
        
        btn_input = Button(ax_btn1, 'Select Input 🎤')
        btn_output = Button(ax_btn2, 'Select Output 🔊')
        btn_start = Button(ax_btn3, 'Start Processing ▶️')
        btn_stop = Button(ax_btn4, 'Stop ⏹️')
        
        btn_input.on_clicked(on_select_input_device)
        btn_output.on_clicked(on_select_output_device)
        btn_start.on_clicked(on_start_processing)
        btn_stop.on_clicked(on_stop_processing)
        
        # Volume and safety indicators
        volume_text_input = ax1.text(0.02, 0.95, '', transform=ax1.transAxes, 
                                   fontsize=10, verticalalignment='top',
                                   bbox=dict(boxstyle='round', facecolor='blue', alpha=0.8))
        
        volume_text_output = ax2.text(0.02, 0.95, '', transform=ax2.transAxes, 
                                    fontsize=10, verticalalignment='top',
                                    bbox=dict(boxstyle='round', facecolor='green', alpha=0.8))
        
        safety_text = ax4.text(0.02, 0.95, '', transform=ax4.transAxes, 
                             fontsize=10, verticalalignment='top',
                             bbox=dict(boxstyle='round', facecolor='orange', alpha=0.8))
        
        def apply_safety_limiting(audio_data):
            """Apply 70dB safety limiting"""
            # Calculate dB level
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms > 0:
                db_level = 20 * np.log10(rms) + 94  # Calibration
            else:
                db_level = -np.inf
            
            # Apply safety limiting
            max_db = 70.0
            if db_level > max_db and db_level != -np.inf:
                reduction_db = db_level - max_db
                reduction_factor = 10 ** (-reduction_db / 20.0)
                processed = audio_data * reduction_factor
            else:
                processed = audio_data.copy()
            
            return processed, db_level
        
        def animate(frame):
            """Animation function with audio processing"""
            if not self.processing_active or not self.stream_input:
                return line_input, line_output, line_freq, line_db
            
            try:
                # Read audio data
                data = self.stream_input.read(CHUNK, exception_on_overflow=False)
                audio_input = np.frombuffer(data, dtype=np.int16) / 32768.0
                
                # Apply safety processing
                audio_output, db_level = apply_safety_limiting(audio_input)
                
                # Send to output device
                if self.stream_output:
                    output_data = (audio_output * 32767).astype(np.int16).tobytes()
                    self.stream_output.write(output_data)
                
                # Update input waveform
                line_input.set_ydata(audio_input)
                
                # Update output waveform
                line_output.set_ydata(audio_output)
                
                # Calculate volumes
                volume_input = np.sqrt(np.mean(audio_input**2))
                volume_output = np.sqrt(np.mean(audio_output**2))
                
                # Update volume displays
                volume_text_input.set_text(f'Input\\nVol: {volume_input:.3f}')
                volume_text_output.set_text(f'Output\\nVol: {volume_output:.3f}')
                
                # Update dB monitoring
                if db_level != -np.inf:
                    self.db_history.append(db_level)
                    self.max_db_recorded = max(self.max_db_recorded, db_level)
                else:
                    self.db_history.append(0)
                
                # Keep last 200 samples
                if len(self.db_history) > 200:
                    self.db_history.pop(0)
                
                # Update dB plot
                time_axis = list(range(len(self.db_history)))
                line_db.set_data(time_axis, self.db_history)
                ax4.set_xlim(0, max(200, len(self.db_history)))
                ax4.set_ylim(0, max(80, self.max_db_recorded + 10))
                
                # Safety status
                current_db = self.db_history[-1] if self.db_history else 0
                if current_db > 70:
                    safety_text.set_text(f'⚠️ {current_db:.1f} dB\\nLIMITING ACTIVE')
                    safety_text.set_bbox(dict(boxstyle='round', facecolor='red', alpha=0.8))
                else:
                    safety_text.set_text(f'✅ {current_db:.1f} dB\\nSAFE LEVEL')
                    safety_text.set_bbox(dict(boxstyle='round', facecolor='green', alpha=0.8))
                
                # Update frequency spectrum
                windowed = audio_input * np.hanning(len(audio_input))
                fft_data = np.fft.fft(windowed)
                magnitude = np.abs(fft_data[:len(fft_data)//2])
                freqs = np.fft.fftfreq(len(fft_data), 1/RATE)[:len(fft_data)//2]
                
                line_freq.set_xdata(freqs)
                line_freq.set_ydata(magnitude)
                
                if magnitude.max() > 0:
                    ax3.set_ylim(0, magnitude.max() * 1.1)
                    
            except Exception as e:
                print(f"Audio processing error: {e}")
                
            return line_input, line_output, line_freq, line_db, volume_text_input, volume_text_output, safety_text
        
        # Initial instructions and auto-selection
        ax_controls.text(0.5, 0.6, "Instructions: Click buttons to cycle devices or auto-select with 'Start'", 
                        ha='center', va='center', fontsize=12,
                        transform=ax_controls.transAxes)
        
        # Auto-select devices on start
        print("🔄 Auto-selecting PC microphone and headphones...")
        auto_select_devices()
        
        # Animation
        ani = animation.FuncAnimation(fig, animate, interval=30, blit=False)
        plt.tight_layout()
        plt.show()
        
        # Cleanup
        if hasattr(self, 'stream_input') and self.stream_input:
            self.stream_input.stop_stream()
            self.stream_input.close()
        if hasattr(self, 'stream_output') and self.stream_output:
            self.stream_output.stop_stream()
            self.stream_output.close()
        p.terminate()

def main():
    """Main function with menu"""
    visualizer = UltimateAudioVisualizer()
    
    print("🎵 Ultimate Audio Visualizer")
    print("=" * 40)
    
    # Check for headphones
    print("🎧 Checking for headphones...")
    if not visualizer.check_headphones():
        print("❌ Exiting. Please connect headphones for the best experience.")
        return
    
    print("Choose an option:")
    print("1. Visualize audio file")
    print("2. Live microphone visualization")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                # File visualization
                if len(sys.argv) > 1:
                    audio_file = sys.argv[1]
                else:
                    # Try to find audio files
                    audio_files = []
                    for ext in ['.wav', '.mp3']:
                        audio_files.extend([f for f in os.listdir('.') if f.lower().endswith(ext)])
                    
                    if audio_files:
                        print("\\nAvailable audio files:")
                        for i, f in enumerate(audio_files):
                            print(f"{i+1}. {f}")
                        
                        try:
                            file_choice = int(input("Choose file number: ")) - 1
                            audio_file = audio_files[file_choice]
                        except:
                            print("Invalid choice, using first file")
                            audio_file = audio_files[0]
                    else:
                        audio_file = input("Enter audio file path: ").strip()
                
                if os.path.exists(audio_file):
                    visualizer.visualize_audio_file(audio_file)
                else:
                    print(f"File not found: {audio_file}")
                    
            elif choice == '2':
                # Microphone visualization
                visualizer.visualize_microphone()
                
            elif choice == '3':
                print("👋 Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
