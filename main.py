import sys
import re
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel,
    QFileDialog, QMessageBox
)

try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False


# --- Convert DMS to Decimal Degrees ---
def dms_to_dd(dms):
    """
    Convert DMS (Degrees, Minutes, Seconds) to Decimal Degrees.
    """
    if pd.isna(dms):
        return None

    dms = str(dms).strip()

    patterns = [
        r"(\d+)[°\s]+(\d+)['\s]+(\d+(?:\.\d+)?)[\"\s]*([NSEWnsew]?)",
        r"(\d+)\s+(\d+)\s+(\d+(?:\.\d+)?)\s*([NSEWnsew]?)",
        r"(\d{2,3})(\d{2})(\d{2}(?:\.\d+)?)([NSEWnsew])",
    ]

    match = None
    for pattern in patterns:
        match = re.match(pattern, dms)
        if match:
            break

    if not match:
        return None

    deg, mins, secs, direction = match.groups()

    try:
        dd = float(deg) + float(mins) / 60 + float(secs) / 3600
        if direction and direction.upper() in ['S', 'W']:
            dd *= -1
        return dd
    except (ValueError, ZeroDivisionError):
        return None


# --- Split combined DMS like "32°14'42.26\"N 7°57'29.36\"W" ---
def split_dms_pair(dms_pair):
    """
    Split combined DMS coordinate like:
    '32°14'42.26"N    7°57'29.36"W' into (lat, lon).
    """
    if pd.isna(dms_pair):
        return None, None

    text = str(dms_pair).strip()
    pattern = r"(\d+°\d+'[\d.]+\"?[NSns])\s*[,\s;]*\s*(\d+°\d+'[\d.]+\"?[EWew])"
    match = re.search(pattern, text)
    if not match:
        return None, None

    lat_str, lon_str = match.groups()
    lat = dms_to_dd(lat_str)
    lon = dms_to_dd(lon_str)
    return lat, lon


# --- Lambert to Decimal Degrees ---
def lambert_to_dd(x, y, lambert_zone="morocco"):
    """
    Convert Lambert coordinates to Decimal Degrees (WGS84).
    """
    if pd.isna(x) or pd.isna(y):
        return None, None

    if not PYPROJ_AVAILABLE:
        return None, None

    try:
        x = float(x)
        y = float(y)

        lambert_zones = {
            "morocco": "EPSG:26191",
            "france": "EPSG:2154",
            "belgium": "EPSG:31370",
            "tunisia": "EPSG:22391",
        }

        source_epsg = lambert_zones.get(lambert_zone.lower(), "EPSG:26191")
        transformer = Transformer.from_crs(source_epsg, "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(x, y)
        return lat, lon
    except Exception:
        return None, None


# --- Check if value is likely DD format ---
def is_decimal_degrees(val):
    """
    Check if a value is already in decimal degrees format.
    Returns True if it's a valid DD coordinate.
    """
    if pd.isna(val):
        return False
    
    # Convert to string and check for DMS indicators
    val_str = str(val).strip()
    
    # If it contains DMS indicators, it's NOT DD
    if any(char in val_str for char in ['°', "'", '"', 'N', 'S', 'E', 'W', 'n', 's', 'e', 'w']):
        return False
    
    # Try to parse as float
    try:
        float_val = float(val)
        # Check if it's in valid DD range (-180 to 180)
        return -180 <= float_val <= 180
    except (ValueError, TypeError):
        return False


# --- Smart Conversion ---
def smart_convert_coordinates(df, x_col, y_col, lambert_zone='morocco'):
    lat_list = []
    lon_list = []
    conversion_types = []

    for idx, row in df.iterrows():
        x_val = row[x_col] if x_col in df.columns else None
        y_val = row[y_col] if y_col in df.columns else None

        x_str = str(x_val).strip() if not pd.isna(x_val) else ""
        y_str = str(y_val).strip() if not pd.isna(y_val) else ""

        # --- Handle combined DMS strings in single column ---
        if not y_str and ('°' in x_str and any(c in x_str.upper() for c in ['N', 'S']) and any(c in x_str.upper() for c in ['E', 'W'])):
            lat, lon = split_dms_pair(x_str)
            lat_list.append(lat)
            lon_list.append(lon)
            conversion_types.append('Combined DMS')
            continue

        # --- Check if BOTH values are already valid decimal degrees ---
        x_is_dd = is_decimal_degrees(x_val)
        y_is_dd = is_decimal_degrees(y_val)
        
        if x_is_dd and y_is_dd:
            try:
                x_float = float(x_val)
                y_float = float(y_val)
                
                # Validate ranges: longitude (-180 to 180), latitude (-90 to 90)
                if -180 <= x_float <= 180 and -90 <= y_float <= 90:
                    # Determine which is lat and which is lon based on range
                    if -90 <= x_float <= 90 and -90 <= y_float <= 90:
                        # Both could be either, assume x=lon, y=lat (standard order)
                        lon_list.append(x_float)
                        lat_list.append(y_float)
                    elif -90 <= x_float <= 90:
                        # x must be latitude
                        lat_list.append(x_float)
                        lon_list.append(y_float)
                    else:
                        # y must be latitude
                        lon_list.append(x_float)
                        lat_list.append(y_float)
                    
                    conversion_types.append('Already DD')
                    continue
            except (ValueError, TypeError):
                pass

        # --- DMS format (separate columns) ---
        if ('°' in x_str or "'" in x_str or '"' in x_str or any(c in x_str.upper() for c in ['N', 'S', 'E', 'W'])) or \
           ('°' in y_str or "'" in y_str or '"' in y_str or any(c in y_str.upper() for c in ['N', 'S', 'E', 'W'])):
            lat = dms_to_dd(y_val)
            lon = dms_to_dd(x_val)
            lat_list.append(lat)
            lon_list.append(lon)
            conversion_types.append('DMS')
            continue

        # --- Lambert coordinates (large numbers) ---
        try:
            x_num = float(x_val)
            y_num = float(y_val)
            # Lambert coordinates are typically very large (> 1000)
            # Also check they're not in valid DD range to avoid false positives
            if (abs(x_num) > 200 or abs(y_num) > 200):
                if PYPROJ_AVAILABLE:
                    lat, lon = lambert_to_dd(x_num, y_num, lambert_zone)
                    lat_list.append(lat)
                    lon_list.append(lon)
                    conversion_types.append('Lambert')
                else:
                    lat_list.append(None)
                    lon_list.append(None)
                    conversion_types.append('Lambert (pyproj missing)')
                continue
        except (ValueError, TypeError):
            pass

        # --- Failed to convert ---
        lat_list.append(None)
        lon_list.append(None)
        conversion_types.append('Failed')

    return lat_list, lon_list, conversion_types


# --- PyQt5 GUI ---
class CoordinateConverter(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Smart Coordinate Converter → GPS Decimal Degrees")
        self.setGeometry(400, 200, 500, 320)

        layout = QVBoxLayout()

        self.label = QLabel("Select Excel file with coordinates:")
        layout.addWidget(self.label)

        self.info_label = QLabel(
            "Auto-detects and converts:\n"
            "• Decimal Degrees (e.g., -7.959712, 32.345678)\n"
            "• DMS format (e.g., 7°57'34.8\"W, 32°20'45\"N)\n"
            "• Combined DMS (e.g., 32°14'42.26\"N 7°57'29.36\"W)\n"
            "• Lambert (e.g., 260088, 186014)\n\n"
            "Expected columns: 'x'/'lon' and 'y'/'lat' or single 'GPS' column"
        )
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(self.info_label)

        if not PYPROJ_AVAILABLE:
            warn = QLabel("⚠️ pyproj not installed - Lambert conversion disabled\nInstall with: pip install pyproj")
            warn.setStyleSheet("color: orange; font-size: 9pt;")
            warn.setWordWrap(True)
            layout.addWidget(warn)

        self.button = QPushButton("Select Excel File")
        self.button.clicked.connect(self.load_excel)
        layout.addWidget(self.button)

        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.setLayout(layout)

    def find_coordinate_columns(self, df):
        lat_col = None
        lon_col = None

        # detect single GPS column
        for col in df.columns:
            if 'gps' in col.lower():
                return col, None

        lat_patterns = ['y', 'lat', 'latitude']
        lon_patterns = ['x', 'lon', 'long', 'longitude']

        columns_lower = {col.lower(): col for col in df.columns}
        for pattern in lat_patterns:
            if pattern in columns_lower:
                lat_col = columns_lower[pattern]
                break
        for pattern in lon_patterns:
            if pattern in columns_lower:
                lon_col = columns_lower[pattern]
                break
        return lat_col, lon_col

    def load_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
        if not file_path:
            return

        try:
            df = pd.read_excel(file_path)
            lat_col, lon_col = self.find_coordinate_columns(df)

            if not lat_col and not lon_col:
                QMessageBox.warning(self, "Column Error", "No coordinate or GPS column found.")
                return

            self.status.setText("Processing... Please wait.")
            QApplication.processEvents()

            if lon_col and lat_col:
                lat_list, lon_list, types = smart_convert_coordinates(df, lon_col, lat_col)
            else:
                lat_list, lon_list, types = smart_convert_coordinates(df, lat_col, lat_col)

            df["Latitude_DD"] = lat_list
            df["Longitude_DD"] = lon_list
            df["Conversion_Type"] = types

            output_path = file_path.rsplit(".", 1)[0] + "_DD.xlsx"
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Sheet1')
                workbook = writer.book
                worksheet = writer.sheets['Sheet1']
                fmt = workbook.add_format({'num_format': '0.00000000'})
                worksheet.set_column('A:Z', 18, fmt)

            success = f"✅ Conversion complete!\nSaved to:\n{output_path}"
            self.status.setText(success)
            QMessageBox.information(self, "Success", success)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.status.setText(f"❌ Error: {e}")


# --- Run app ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoordinateConverter()
    window.show()
    sys.exit(app.exec_())