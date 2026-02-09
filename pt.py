import sys
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog,
    QLabel, QMessageBox, QComboBox
)

class ExcelMerger(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel Merger - Left Join")
        self.resize(450, 350)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # --- File A ---
        self.btnA = QPushButton("Select Excel A (Main File)")
        self.btnA.clicked.connect(self.load_excel_a)
        self.layout.addWidget(self.btnA)

        self.labelA = QLabel("No file selected")
        self.layout.addWidget(self.labelA)

        self.comboA = QComboBox()
        self.layout.addWidget(self.comboA)
        self.comboA.setEnabled(False)

        # --- File B ---
        self.btnB = QPushButton("Select Excel B (File to Merge)")
        self.btnB.clicked.connect(self.load_excel_b)
        self.layout.addWidget(self.btnB)

        self.labelB = QLabel("No file selected")
        self.layout.addWidget(self.labelB)

        self.comboB = QComboBox()
        self.layout.addWidget(self.comboB)
        self.comboB.setEnabled(False)

        # --- Merge button ---
        self.btnMerge = QPushButton("Merge and Save (Left Join)")
        self.btnMerge.clicked.connect(self.merge_excels)
        self.layout.addWidget(self.btnMerge)

        # Data holders
        self.dfA = None
        self.dfB = None

    def load_excel_a(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel A", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.dfA = pd.read_excel(path)
            self.labelA.setText(f"Loaded: {path.split('/')[-1]}")
            self.comboA.clear()
            self.comboA.addItems(self.dfA.columns)
            self.comboA.setEnabled(True)
            self.fileA_path = path

    def load_excel_b(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel B", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.dfB = pd.read_excel(path)
            self.labelB.setText(f"Loaded: {path.split('/')[-1]}")
            self.comboB.clear()
            self.comboB.addItems(self.dfB.columns)
            self.comboB.setEnabled(True)
            self.fileB_path = path

    def merge_excels(self):
        if self.dfA is None or self.dfB is None:
            QMessageBox.warning(self, "Error", "Please select both Excel files first.")
            return

        keyA = self.comboA.currentText()
        keyB = self.comboB.currentText()

        try:
            merged = pd.merge(self.dfA, self.dfB, how="left", left_on=keyA, right_on=keyB)

            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save Merged File", "merged.xlsx", "Excel Files (*.xlsx)"
            )
            if save_path:
                merged.to_excel(save_path, index=False)
                QMessageBox.information(self, "Success", f"File saved:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Merge Error", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExcelMerger()
    window.show()
    sys.exit(app.exec_())
