import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QSlider, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt

class MotorEstimator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIXR-1 Motor Digital Twin")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #0d1117; color: #c9d1d9; font-size: 14px;")

        # Motor Constants from Graph
        self.NO_LOAD_RPM = 650.0
        self.STALL_TORQUE = 6.7
        self.NO_LOAD_AMP = 0.071
        self.STALL_AMP = 0.72

        layout = QVBoxLayout(self)

        # Output Display
        display_group = QGroupBox("Estimated Operating Parameters")
        display_group.setStyleSheet("QGroupBox { border: 2px solid #30363d; border-radius: 6px; padding: 15px; font-weight: bold; }")
        form_layout = QFormLayout(display_group)

        self.lbl_rpm = QLabel("600 RPM")
        self.lbl_rpm.setStyleSheet("color: #58a6ff; font-size: 24px; font-weight: bold;")
        
        self.lbl_amps = QLabel("0.000 A")
        self.lbl_amps.setStyleSheet("color: #ff7b72; font-size: 20px; font-weight: bold;")
        
        self.lbl_torque = QLabel("0.000 kg-mm")
        self.lbl_torque.setStyleSheet("color: #3fb950; font-size: 20px; font-weight: bold;")

        form_layout.addRow("Target Speed:", self.lbl_rpm)
        form_layout.addRow("PSU Current:", self.lbl_amps)
        form_layout.addRow("Fluid Drag:", self.lbl_torque)
        layout.addWidget(display_group)

        # Slider Input
        slider_layout = QVBoxLayout()
        slider_label = QLabel("Scroll Target RPM (0 to 650)")
        
        self.rpm_slider = QSlider(Qt.Orientation.Horizontal)
        self.rpm_slider.setRange(0, 650)
        self.rpm_slider.setValue(600)
        self.rpm_slider.setStyleSheet("QSlider::handle:horizontal { background: #58a6ff; width: 16px; margin: -5px 0; border-radius: 8px; } QSlider::groove:horizontal { background: #30363d; height: 6px; border-radius: 3px; }")
        
        self.rpm_slider.valueChanged.connect(self.calculate_metrics)
        
        slider_layout.addWidget(slider_label)
        slider_layout.addWidget(self.rpm_slider)
        layout.addLayout(slider_layout)

        # Run initial calculation
        self.calculate_metrics(600)

    def calculate_metrics(self, rpm: int):
        self.lbl_rpm.setText(f"{rpm} RPM")

        # 1. Reverse-engineer Torque from RPM
        torque = (self.NO_LOAD_RPM - rpm) * (self.STALL_TORQUE / self.NO_LOAD_RPM)
        
        # 2. Calculate Current from Torque
        amps = self.NO_LOAD_AMP + (torque * ((self.STALL_AMP - self.NO_LOAD_AMP) / self.STALL_TORQUE))

        self.lbl_torque.setText(f"{torque:.3f} kg-mm")
        self.lbl_amps.setText(f"{amps:.3f} A")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MotorEstimator()
    window.show()
    sys.exit(app.exec())