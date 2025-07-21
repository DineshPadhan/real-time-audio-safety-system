---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''

---

**🐛 Bug Description**
A clear and concise description of what the bug is.

**🔄 Steps to Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**✅ Expected Behavior**
A clear and concise description of what you expected to happen.

**📱 System Information**
- **OS**: [e.g. Windows 11, Ubuntu 20.04]
- **Python Version**: [e.g. 3.13.5]
- **Audio Hardware**: [e.g. USB headphones, Bluetooth headset]
- **Dependencies**: Run `pip list | findstr "pyaudio numpy matplotlib"`

**📋 Audio Device Information**
Run this command and paste the output:
```bash
python -c "import pyaudio; p=pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]; p.terminate()"
```

**📸 Screenshots/Error Messages**
If applicable, add screenshots or paste error messages to help explain your problem.

**🔧 Additional Context**
Add any other context about the problem here.

**🎧 Headphone Connection Status**
- [ ] Headphones are connected and working
- [ ] Tested with different headphones
- [ ] Issue occurs with/without headphones
