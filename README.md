# 🌍 GeoConverter Pro

**A professional-grade Python utility for intelligent coordinate transformation and normalization.**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyQt5](https://img.shields.io/badge/UI-PyQt5-orange.svg)](https://www.riverbankcomputing.com/software/pyqt/)

## 🚀 Overview
GeoConverter Pro is a lightweight, high-performance desktop tool designed to solve the "coordinate mess" often found in GIS datasets. It automatically detects and converts various geographic coordinate formats from Excel files into standardized **WGS84 Decimal Degrees**.

## ✨ Key Features
- **Smart Detection**: Automatically identifies if your data is DMS, DD, or Lambert.
- **Lambert Projections**: Native support for **Morocco** (EPSG:26191), **France** (EPSG:2154), **Belgium** (EPSG:31370), and **Tunisia** (EPSG:22391).
- **Auto-Mapping**: Finds coordinate columns named 'lat', 'longitude', 'x', 'y', or 'gps' automatically.
- **Robust Parsing**: Handles complex strings like `32°14'42.26"N 7°57'29.36"W` found in messy reports.
- **Batch Export**: Generates a new Excel file with high-precision outputs (up to 8 decimal places).

## 🛠 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/geoconverter-pro.git
cd geoconverter-pro
```

### 2. Install dependencies
```bash
pip install pandas openpyxl PyQt5 pyproj xlsxwriter
```
*Note: `pyproj` is required for Lambert transformations.*

## 📖 Usage
1. Launch the application:
   ```bash
   python main.py
   ```
2. Click **"Select Excel File"**.
3. Choose your `.xlsx` or `.xls` file.
4. The tool will process all rows and save a new file suffixed with `_DD.xlsx` in the same directory.

## 🌍 Supported Formats
| Type | Example Input |
| :--- | :--- |
| **Decimal Degrees** | `32.34567, -7.95971` |
| **DMS (Standard)** | `32°20'45"N, 7°57'34"W` |
| **Combined DMS** | `32°14'42"N 7°57'29"W` |
| **Lambert (Grid)** | `260088, 186014` |

## 🧪 Technical Details
- **Core Engine**: Built on `pandas` for data manipulation and `pyproj` for geodetic transformations.
- **UI Framework**: Responsive desktop interface powered by `PyQt5`.
- **Logic**: Uses regex patterns to tokenize and normalize non-standard DMS strings.

## 📜 License
This project is licensed under the MIT License - see the LICENSE file for details.

---
*Created By Ayyoub Dahir with ❤️ for the GIS Community.*
