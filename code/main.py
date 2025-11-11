import serial
import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QPushButton, QTextEdit, QLabel, QDialog, 
                           QLineEdit, QDialogButtonBox, QSpinBox, QMessageBox,
                           QListWidget, QSplitter, QFrame, QStatusBar, QScrollArea,
                           QInputDialog, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor, QIcon, QTextCharFormat

class ModeSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FRAM Manager - Mode Selection")
        self.setFixedSize(400, 300)
        self.mode = None
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("Choose Application Mode")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        desc = QLabel("Select your preferred interface:")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #7f8c8d; margin-bottom: 10px;")
        layout.addWidget(desc)
        
        gui_btn = QPushButton("🎨  GUI Mode")
        gui_btn.setToolTip("Visual interface with buttons")
        gui_btn.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                padding: 15px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        gui_btn.clicked.connect(self.select_gui)
        layout.addWidget(gui_btn)
        
        terminal_btn = QPushButton("💻  Terminal Mode")
        terminal_btn.setToolTip("Command-line interface")
        terminal_btn.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                padding: 15px;
                background-color: #2c3e50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
        """)
        terminal_btn.clicked.connect(self.select_terminal)
        layout.addWidget(terminal_btn)
        
        info = QLabel("GUI: Buttons and visual interface\nTerminal: Type commands directly")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet("color: #95a5a6; font-size: 9pt; margin-top: 10px;")
        layout.addWidget(info)
        
        self.setLayout(layout)
    
    def select_gui(self):
        self.mode = "GUI"
        self.accept()
    
    def select_terminal(self):
        self.mode = "TERMINAL"
        self.accept()

class SerialThread(QThread):
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, port='COM6', baudrate=115200): #change the COM6 port to the one you are using
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.ser = None
        self.running = True
        
    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.data_received.emit("READY: Connected to Teensy")
            
            while self.running:
                if self.ser and self.ser.in_waiting > 0:
                    data = self.ser.readline().decode('utf-8', errors='replace').strip()
                    if data:
                        self.data_received.emit(data)
        except Exception as e:
            self.error_occurred.emit(f"Serial error: {e}")
            
    def send_command(self, command):
        if self.ser and self.ser.is_open:
            try:
                print(f"Sending command: '{command}'")  # Debug
                self.ser.write(f"{command}\n".encode())
                return True
            except Exception as e:
                self.error_occurred.emit(f"Send error: {e}")
                return False
        return False
                
    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()

class TerminalWidget(QTextEdit):
    command_entered = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setFont(QFont("Consolas", 10))
        self.setPlaceholderText("Type commands here (help, ERASE, WRITE:data, READ:bytes, EXPORT)...")
        
        # Set dark theme
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))
        self.setPalette(palette)
        
        self.command_start_pos = 0
        self.update_prompt()
        
    def update_prompt(self):
        self.moveCursor(QTextCursor.MoveOperation.End)
        self.insertPlainText("FRAM> ")
        self.command_start_pos = self.textCursor().position()
        
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            cursor.setPosition(self.command_start_pos)
            cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
            raw_text = cursor.selectedText()
            
            command = self.clean_command(raw_text)
            
            if command:
                self.append("")
                self.command_entered.emit(command)
            
            self.update_prompt()
            return
            
        elif event.key() == Qt.Key.Key_Backspace:
            cursor = self.textCursor()
            if cursor.position() <= self.command_start_pos:
                return
                
        super().keyPressEvent(event)
    
    def clean_command(self, raw_text):
        if raw_text.startswith("FRAM> "):
            raw_text = raw_text[6:]
        
        import re
        cleaned = re.sub(r'[\u0000-\u001F\u007F-\u009F\u2000-\u20FF\u2600-\u26FF\u2700-\u27BF]', '', raw_text)
        cleaned = re.sub(r'\d{2}:\d{2}:\d{2}', '', cleaned)
        cleaned = re.sub(r'[➡️❌✅ℹ️]', '', cleaned)
        
        cleaned = ' '.join(cleaned.split()).strip()
        
        return cleaned

class ConsoleWidget(QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(0, 255, 0))
        self.setPalette(palette)
        
    def append_message(self, message, color="#00ff00"):
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)
        cursor.insertText(message + "\n")
        
        self.moveCursor(QTextCursor.MoveOperation.End)

class TerminalModeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_thread = None
        self.setup_ui()
        self.connect_teensy()
        
    def setup_ui(self):
        self.setWindowTitle("FRAM Manager - Terminal Mode")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("💻 FRAM Manager - Terminal Mode")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px; color: #e74c3c;")
        layout.addWidget(header)
        
        instructions = QLabel("Type commands below. Type 'help' for available commands.")
        instructions.setStyleSheet("font-size: 10pt; color: #95a5a6; margin: 5px;")
        layout.addWidget(instructions)
        
        self.terminal = TerminalWidget()
        layout.addWidget(self.terminal)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Terminal Mode - Ready for commands")
        
    def connect_teensy(self):
        """Establish connection to Teensy"""
        try:
            self.serial_thread = SerialThread()
            self.serial_thread.data_received.connect(self.handle_serial_data)
            self.serial_thread.error_occurred.connect(self.handle_serial_error)
            self.serial_thread.start()
            
            self.terminal.command_entered.connect(self.handle_terminal_command)
            self.log_to_terminal("Connected to Teensy. Type 'help' for commands.", "info")
        except Exception as e:
            self.log_to_terminal(f"Connection error: {e}", "error")
    
    def handle_serial_data(self, data):
        """Handle incoming serial data"""
        self.log_to_terminal(data, "response")
    
    def handle_serial_error(self, error):
        """Handle serial errors"""
        self.status_bar.showMessage(f"Error: {error}")
        self.log_to_terminal(f"Serial error: {error}", "error")
    
    def log_to_terminal(self, message, msg_type="info"):
        """Log message to terminal"""
        time = datetime.now().strftime("%H:%M:%S")
        
        cursor = self.terminal.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        
        format = QTextCharFormat()
        if msg_type == "error":
            format.setForeground(QColor("#ff4444"))
            prefix = "❌"
        elif msg_type == "success":
            format.setForeground(QColor("#44ff44"))
            prefix = "✅"
        elif msg_type == "response":
            format.setForeground(QColor("#ffff44"))
            prefix = "➡️"
        else:
            format.setForeground(QColor("#ffff44"))
            prefix = "ℹ️"
            
        cursor.setCharFormat(format)
        cursor.insertText(f"{time} {prefix} {message}\n")
        
        self.terminal.moveCursor(QTextCursor.MoveOperation.End)
    
    def handle_terminal_command(self, command):
        """Handle commands entered in terminal"""
        else:
            formatted_command = self.format_command_for_arduino(command)
            
            if self.serial_thread and self.serial_thread.isRunning():
                self.log_to_terminal(f"Executing: {formatted_command}", "info")
                success = self.serial_thread.send_command(formatted_command)
                if not success:
                    self.log_to_terminal("Failed to send command to microcontroller", "error")
            else: 
                self.log_to_terminal("Not connected to microcontroller", "error")
    
    def format_command_for_arduino(self, command):
        """Convert user-friendly command to Arduino-compatible format"""
        command = command.upper().strip()
        
        if command.startswith("READ "):
            parts = command.split()
            if len(parts) >= 2:
                return f"READ:{parts[1]}"
        
        elif command.startswith("WRITE "):
            parts = command.split(' ', 1) 
            if len(parts) >= 2:
                return f"WRITE:{parts[1]}"
        
        return command
    
    def show_help(self):
        """Display help information"""
        help_text = """
Available Commands (Arduino Format):
───────────────────────────────────
ERASE           - Erase entire FRAM memory
WRITE:data      - Write text data to FRAM (e.g., WRITE:Hello World)
READ:bytes      - Read specified number of bytes (e.g., READ:256)
EXPORT          - Export FRAM contents as hex dump

User-Friendly Input:
────────────────────
You can type:
- 'read 256' or 'READ:256'  
- 'write hello' or 'WRITE:hello'
- 'erase' or 'ERASE'
- 'export' or 'EXPORT'

Examples:
─────────
ERASE
WRITE This is test data
READ 100
EXPORT

help            - Show this help message
exit, quit      - Exit the application
"""
        self.log_to_terminal(help_text, "info")
    
    def closeEvent(self, event):
        """Handle application closure"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait(2000)
        event.accept()


class GUIModeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_thread = None
        self.setup_ui()
        self.connect_teensy()
        
    def setup_ui(self):
        self.setWindowTitle("FRAM Manager - GUI Mode")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QLabel("🎨 FRAM Manager - GUI Mode")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px; color: #3498db;")
        layout.addWidget(header)
        
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        buttons_data = [
            ("🗑 Erase FRAM", self.erase_fram, "#dc3545"),
            ("💾 Write FRAM", self.write_fram, "#007bff"),
            ("📖 Read FRAM", self.read_fram, "#28a745"),
            ("📤 Export FRAM", self.export_fram, "#ffc107")
        ]
        
        for text, callback, color in buttons_data:
            btn = QPushButton(text)
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: 11pt;
                    padding: 12px;
                    background-color: {color};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    min-width: 120px;
                }}
                QPushButton:hover {{
                    background-color: {self.lighten_color(color)};
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color)};
                }}
            """)
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)
        
        layout.addWidget(button_frame)
        
        console_label = QLabel("Activity Log (Read-Only)")
        console_label.setStyleSheet("font-size: 12pt; font-weight: bold; margin-top: 15px;")
        layout.addWidget(console_label)
        
        self.console = ConsoleWidget()
        layout.addWidget(self.console)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("GUI Mode - Ready")
    
    def lighten_color(self, hex_color):
        """Lighten a hex color"""
        r = min(255, int(hex_color[1:3], 16) + 30)
        g = min(255, int(hex_color[3:5], 16) + 30)
        b = min(255, int(hex_color[5:7], 16) + 30)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def darken_color(self, hex_color):
        """Darken a hex color"""
        r = max(0, int(hex_color[1:3], 16) - 30)
        g = max(0, int(hex_color[3:5], 16) - 30)
        b = max(0, int(hex_color[5:7], 16) - 30)
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def connect_teensy(self):
        """Establish connection to Teensy"""
        try:
            self.serial_thread = SerialThread()
            self.serial_thread.data_received.connect(self.handle_serial_data)
            self.serial_thread.error_occurred.connect(self.handle_serial_error)
            self.serial_thread.start()
            self.console.append_message("Connected to Teensy. Use buttons to control FRAM.", "#44ff44")
        except Exception as e:
            self.console.append_message(f"Connection error: {e}", "#ff4444")
    
    def handle_serial_data(self, data):
        """Handle incoming serial data"""
        if "READY:" in data:
            self.status_bar.showMessage("Connected to Teensy - FRAM Ready")
        
        if "ERROR" in data:
            color = "#ff4444"
        elif "WRITTEN" in data or "ERASED" in data or "READY" in data:
            color = "#44ff44"
        else:
            color = "#ffff44"
            
        self.console.append_message(data.strip(), color)
    
    def handle_serial_error(self, error):
        """Handle serial errors"""
        self.status_bar.showMessage(f"Error: {error}")
        self.console.append_message(f"ERROR: {error}", "#ff4444")
    
    def erase_fram(self):
        """Erase FRAM memory"""
        if self.serial_thread:
            self.console.append_message("Sending ERASE command...", "#ffff44")
            self.serial_thread.send_command("ERASE")
    
    def write_fram(self):
        """Write data to FRAM"""
        data, ok = QInputDialog.getText(self, "Write FRAM", "Enter data to save:")
        if ok and data:
            self.console.append_message(f"Writing data: '{data}'", "#ffff44")
            self.serial_thread.send_command(f"WRITE:{data}")
    
    def read_fram(self):
        """Read data from FRAM"""
        n, ok = QInputDialog.getInt(self, "Read FRAM", "Bytes to read:", 256, 1, 32768)
        if ok:
            self.console.append_message(f"Reading {n} bytes...", "#ffff44")
            self.serial_thread.send_command(f"READ:{n}")
    
    def export_fram(self):
        """Export FRAM contents to file"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export FRAM", "fram_export.txt", "Text Files (*.txt)"
        )
        if filename:
            if not filename.endswith('.txt'):
                filename += '.txt'
            self.console.append_message(f"Exporting to {filename}...", "#ffff44")
            self.serial_thread.send_command("EXPORT")
    
    def closeEvent(self, event):
        """Handle application closure"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.serial_thread.wait(2000)
        event.accept()

class FRAMManager:
    def __init__(self):
        self.mode = None
        
    def run(self):
        """Main entry point with mode selection"""
        app = QApplication(sys.argv)
        
        dialog = ModeSelectionDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if dialog.mode == "GUI":
                window = GUIModeWindow()
                window.show()
                sys.exit(app.exec())
            else:  # TERMINAL mode
                window = TerminalModeWindow()
                window.show()
                sys.exit(app.exec())
        else:
            sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--terminal", "-t"]:
        app = QApplication(sys.argv)
        window = TerminalModeWindow()
        window.show()
        sys.exit(app.exec())
    elif len(sys.argv) > 1 and sys.argv[1] in ["--gui", "-g"]:
        app = QApplication(sys.argv)
        window = GUIModeWindow()
        window.show()
        sys.exit(app.exec())
    else:
        manager = FRAMManager()
        manager.run()
