# Multi-Modal Durian Fruit Ripeness Dataset

## Overview

This dataset contains comprehensive multi-modal sensor data for 189 durian fruit (*Durio zibethinus*) samples collected from **Belviz Farms, Brgy Wangan, Calinan, Davao City, Philippines** during the 2025 harvest season. The dataset includes synchronized measurements from four distinct sensor modalities: multispectral imaging, RGB imaging, thermal imaging, and acoustic knock recordings. This collection enables research into non-destructive fruit ripeness assessment and maturity classification.

**Dataset Collection Period:** September 5 – November 24, 2025

---

## Experimental Design

### Sample Population
- **Total Samples:** 189 durian fruits
- **Maturity Stages:** 3 (Immature, Mature, Post-Mature)
- **Ripeness Classes:** 3 per stage (Unripe, Ripe, Overripe)
- **Replicates:** ~7 per category

### Spatial Coverage
Each sample was imaged and acoustically recorded from 6 distinct orientations:
- **TOP** – Apex of fruit
- **BOT** – Bottom/base of fruit  
- **SA, SB, SC, SD** – Side angles (roughly 90° intervals around circumference)

### Temporal Measurements
Samples were tracked at three critical ripeness stages:
- **Harvest** – Initial state at collection
- **End of Storage (EOS)** – After 2-3 weeks cold storage (4-5°C)
- **Post-Storage** – After ripening at room temperature

---

## Dataset Structure

```
datasets/
├── dataset_clean_multispectral/
│   ├── metadata.csv
│   ├── *.tif (GeoTIFF multispectral montages, 189 files)
│   └── [technical specifications below]
│
├── dataset_clean_rgb/
│   ├── metadata.csv
│   ├── *.jpg (RGB photographs, 1,134 files: 189 samples × 6 orientations)
│   └── [technical specifications below]
│
├── dataset_clean_thermal/
│   ├── metadata.csv
│   ├── *.jpg (Thermal images, 1,134 files)
│   ├── *.csv (Thermal data matrices, 1,134 files)
│   └── [technical specifications below]
│
└── dataset_clean_sound/
    ├── metadata.csv
    ├── *.m4a (iPhone audio files, ~189 files)
    ├── *.wav (Android audio files, ~189 files)
    └── [technical specifications below]
```

---

## Sensor Specifications & Data Formats

### 1. Multispectral Imaging

**Hardware:** Tetracam MSC2-NIR8-1-A
- **Bands:** 8 spectral bands (720–980 nm near-infrared range)
- **Spatial Resolution:** 256 × 256 pixels per band
- **Output Format:** GeoTIFF (co-registered, geo-referenced)
- **Montage Layout:** 1024 × 512 pixels (4 bands top orientation + 4 bands bottom orientation side-by-side)
- **File Size:** ~15–20 MB per sample (compressed)
- **Number of Files:** 189 (one composite per sample, not per orientation)

**Data Structure:**
- Each TIF contains spectral signatures across full near-infrared spectrum
- Georeferenced metadata embedded in TIFF headers
- Suitable for vegetation indices (NDVI, NDBI, etc.) and ripeness spectral analysis

**Metadata CSV Columns:**
- `sample_num`, `maturity`, `class`, `ripeness`
- Band references and processing notes

---

### 2. RGB Imaging

**Hardware:** Canon EOS R50 & Canon EOS M50 Mark II
- **Output Format:** JPEG (RGB 8-bit)
- **Resolution:** ~6000 × 4000 pixels (varies by camera model)
- **File Size:** 5.3–8.3 MB per image
- **Number of Files:** 1,134 (189 samples × 6 orientations)
- **Color Space:** sRGB

**Data Collection:**
- Controlled lighting environment
- Consistent distance and angle per orientation
- Camera switched from Canon R50 to M50 Mark II during collection period

**Metadata CSV Columns:**
- `sample_num`, `maturity`, `class`, `orientation` (TOP, BOT, SA, SB, SC, SD)
- `ripeness`, `date_captured`, `source_folder`, `new_filename`, `file_size`
- `cleaned` status (data quality flag)

---

### 3. Thermal Imaging

**Hardware:** Fotric 323F Thermal Camera + AnalyzIR Software
- **Output Format:** 
  - JPEG thermal image (false-color representation)
  - CSV data matrix (temperature values in °C)
- **Sensor Resolution:** 1024 × 1024 pixels
- **Temperature Range:** Calibrated for ambient to warm fruit (0–60°C typical)
- **File Size:** ~600 KB JPG + ~1 MB CSV per image
- **Number of Files:** 2,268 (189 samples × 6 orientations × 2 formats)

**Data Structure:**
- **CSV Format:** Rows represent pixel rows; columns represent pixel columns; values are temperature in °C
- Each CSV corresponds to one thermal image (same orientation and sample)
- JPG provides visual reference; CSV enables quantitative thermal analysis

**Metadata CSV Columns:**
- `sample_num`, `maturity`, `class`, `orientation`, `ripeness`
- `date_captured`, `new_filename_jpg`, `new_filename_csv`
- `jpg_size`, `csv_size`, `file_type` (thermal_jpg / thermal_csv)

---

### 4. Acoustic Recordings (Knock Tests)

**Hardware:** 
- **iPhone 13** – Built-in microphone (M4A format)
- **Redmi Note 14** – Built-in microphone (WAV format)

**Specifications:**
- **Sample Rate:** 48 kHz (both devices)
- **Audio Format:** 
  - iPhone: M4A (AAC codec, ~128 kbps)
  - Android: WAV (16-bit PCM, ~1.5 Mbps)
- **Recording Duration:** ~30 seconds per recording
- **File Size:** 1.1–2.0 MB (iPhone M4A) | 5.5–9.7 MB (Android WAV)
- **Number of Files:** ~378 total (~2 recordings per sample, some with redundant attempts)

**Recording Protocol:**
- **Knock Method:** Rubber-tipped stick (standardized impact tool)
- **Recording Distance:** 5 inches from fruit surface
- **Knocks per Session:** 3 consecutive taps per area/orientation
- **Microphone Placement:** Near fruit surface for acoustic resonance capture

**Use Case:** Acoustic signatures correlate with internal ripeness and structural changes during maturation.

**Metadata CSV Columns:**
- `sample_num` – Standardized 3-digit sample identifier
- `ripeness` – Unripe, Ripe, or Overripe
- `iphone_original` – Original iPhone M4A filename
- `iphone_date` – iPhone recording timestamp (YYYY-MM-DD HH:MM:SS)
- `iphone_size_bytes` – iPhone audio file size in bytes
- `iphone_output` – Standardized iPhone M4A output filename
- `android_original` – Original Android WAV filename
- `android_date` – Android recording timestamp (YYYY-MM-DD HH:MM:SS)
- `android_size_bytes` – Android audio file size in bytes
- `android_output` – Standardized Android WAV output filename

---

## File Organization & Naming Conventions

### Sample Identification
Each sample is identified by a 3-digit number and maturity/class labels:
- **Format:** `durian_XXX_[Maturity]_[Class]_[Ripeness]`
- **Example:** `durian_045_Mature_B_Ripe`
- **Maturity:** Immature, Mature, Post-Mature
- **Class:** A, B, C (internal classification)
- **Ripeness:** Unripe, Ripe, Overripe

### Orientation Abbreviations
- `TOP` – Top/apex
- `BOT` – Bottom/base
- `SA`, `SB`, `SC`, `SD` – Side angles

### File Naming Examples
- Multispectral: `durian_045_Mature_B_Ripe_COMBINED.tif`
- RGB: `durian_045_Mature_B_Ripe_TOP.jpg`
- Thermal JPG: `durian_045_Mature_B_Ripe_BOT_thermal.jpg`
- Thermal CSV: `durian_045_Mature_B_Ripe_BOT_thermal.csv`
- Audio: `45-R.m4a` (iPhone) or `MA_CB_R_45.wav` (Android)

---

## Metadata Files

Each modality folder contains a `metadata.csv` file documenting all corresponding data files:

### Universal Columns (across all metadata files)
- `sample_num` – Standardized 3-digit or full sample identifier
- `maturity` – Immature, Mature, or Post-Mature
- `class` – A, B, or C classification
- `ripeness` – Unripe, Ripe, or Overripe
- `date_captured` – Collection date (YYYY-MM-DD format)

### Modality-Specific Columns
- **Multispectral:** Band references, georeferencing metadata
- **RGB:** Orientation, file size, source camera, cleaned status
- **Thermal:** Orientation, JPG/CSV file sizes, temperature range
- **Acoustic:** iPhone and Android file pairs, device-specific metadata

---

## Data Quality & Completeness

- **Coverage:** All 189 samples have corresponding files across all four modalities
- **RGB Completeness:** 100% (6 orientations per sample, 1,134 total files)
- **Thermal Completeness:** 100% (both JPG and CSV pairs, 2,268 files)
- **Audio Completeness:** >95% (most samples have dual recordings; some have redundant attempts from different collection dates)
- **Multispectral Completeness:** 100% (composite montage per sample, 189 files)

### Known Data Notes
- Some audio samples have multiple recordings from different dates (retry attempts for quality assurance)
- Two RGB cameras used (Canon R50 → M50 Mark II); file sizes vary slightly between devices
- All date/time stamps in UTC+8 (Asia/Bangkok timezone, original collection region)

---

## Usage & Access

### File Access
- All files are organized in modality-specific subdirectories
- Use the `sample_num` column in metadata CSVs to cross-reference files across modalities
- All filenames are standardized and programmatically parseable

### Recommended Workflow
1. Start with **metadata CSV files** to understand sample organization and collection dates
2. Use **thermal CSV files** for quantitative temperature analysis
3. Use **RGB images** for visual verification and color-based analysis
4. Use **acoustic CSV files** for structural ripeness assessment
5. Use **multispectral data** for advanced spectral analysis and vegetation indices

### File Format Compatibility
- **GeoTIFF:** GDAL, ENVI, QGIS, Python (rasterio, gdal)
- **JPEG:** Standard image viewers; Python (PIL, opencv)
- **CSV (Thermal):** Any spreadsheet or data analysis software; R, Python, MATLAB
- **Audio (M4A/WAV):** Standard audio players; Python (librosa, soundfile), MATLAB (audioread)

---

## Storage Requirements

| Modality | File Count | Total Size | Compression |
|----------|-----------|-----------|-------------|
| Multispectral | 189 | ~973.58 GB | GeoTIFF (compressed) |
| RGB | 1,134 | ~20.28 GB | JPEG |
| Thermal (JPG+CSV) | 1,134 | ~536.34 GB | JPEG + Uncompressed text |
| Audio (iPhone + Android) | ~189 | ~1.62 GB | M4A (AAC) + WAV (PCM) |
| **TOTAL** | **~4,700** | **~23.42 GB** | Mixed formats |

*Total size as reported by Zenodo (doi.org/10.5281/zenodo.18603796).*

---

## Citation

If you use this dataset in your research, please cite it as:

```
Mesa-Satina, A. R., Kobayashi, V. B., Bayogan, E. R., & Calag, V. B. (2026). Multi-Modal Sensor Data for Durian Fruit Maturity Classification and Ripeness Assessment. Zenodo. https://doi.org/10.5281/zenodo.18603796
```

**Dataset DOI:** 10.5281/zenodo.18603796

This dataset is archived on Zenodo for long-term preservation and open access. It encompasses multi-spectral, thermal, RGB, and acoustic data for non-destructive ripeness and maturity assessment of durian fruit.

---

## License

### Data License: CC BY 4.0 (Creative Commons Attribution 4.0 International)

You are free to:
- **Share** – Copy and redistribute the material in any medium or format
- **Adapt** – Remix, transform, and build upon the material for any purpose, even commercially

Under the following terms:
- **Attribution** – You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in a way that suggests the licensor endorses you or your use.

### Full License Text
See [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/) for the complete legal text.

### Research Ethics
- This dataset was collected in compliance with institutional guidelines for agricultural research
- No human subjects or protected species were harmed in data collection
- Equipment used complies with local regulations for produce handling

---

## Contact & Support

For questions, corrections, or data access issues:
- **Project:** AI-based Non-Invasive Grading System for Durian (AIDurian)
- **Project Lead:** Assoc. Prof. Armacheska R. Mesa-Satina, PhD
- **Institution:** University of the Philippines Mindanao, College of Science and Mathematics, Department of Mathematics, Physics, and Computer Science
- **Zenodo Record:** https://zenodo.org/records/18603796 (DOI: 10.5281/zenodo.18603796)

---

## Acknowledgments

### Funding & Support

This project was supported by the **Department of Science and Technology - Philippine Council for Agriculture, Aquatic and Natural Resources Research and Development (DOST-PCAARRD)** through the **Accelerated R&D Program for Capacity Building of Research and Development Institutions and Industrial Competitiveness: Industry-Level Collaborative Research and Development to Leverage Philippines Economy (I-CRADLE) Program**.

**Project Details:**
- **Project Title:** AI-based Non-Invasive Grading System for Durian (AIDurian)
- **Duration:** 2023-2026
- **Funding Agency:** Department of Science and Technology - Philippine Council for Agriculture, Aquatic and Natural Resources Research and Development (DOST-PCAARRD)

**Research Team:**
- Assoc. Prof. Armacheska R. Mesa-Satina, PhD (Project Lead)
- Prof. Vladimer B. Kobayashi, PhD (Project Staff)
- Prof. Emma Ruth Bayogan, PhD (Project Staff)
- Asst. Prof. Vicente B. Calag, MSCS, MICT (Project Staff)
- Jenno Fred M. Villarino (Project Technical Specialist)
- Junniel Rome A. Ardepuela (Project Technical Specialist)
- Michael Angela J. Urquiola (Project Technical Specialist)
- Mary Jean T. Recla (Administrative Aide)

### Collaborative Partners & Industry Stakeholders

The project acknowledges the critical participation of its partner agencies and industry collaborators:
- **Durian Industry Association of Davao City** – Supporting coordination among stakeholders and providing inputs on sector needs and market requirements
- **Belviz Farms** – Providing access to field environments and facilitating the acquisition and handling of fruit samples
- **Rosario's Delicacies** – Supporting operational insights and documentation of grading practices
- **D'Farmers Market** – Contributing to practical validation in real-world settings
- **VJT Enterprises** – Providing industry perspectives on processing and marketing operations
- **Eng Seng** – Supporting industry-level collaboration and coordination

These partners ensured that the project was grounded in real operational needs and practical conditions within the durian industry, moving the research beyond laboratory-level development toward practical deployment and validation.

### Government & Supporting Institutions

- **DOST Region XI** – Supporting local coordination and facilitating linkages with regional stakeholders
- **Department of Trade and Industry (DTI)** – Supporting pathways for adoption, scaling, and eventual commercialization of the developed system
- **Department of Agriculture – Bureau of Plant Identity (DA-BPI)** – Providing technical reference on quality standards and regulatory frameworks
- **Regional Development Council XI** – Endorsing the initiative and supporting alignment with regional development priorities

### Research Support Staff

Special recognition is given to the research assistants, students, and technical staff whose commitment and sustained effort contributed to the successful completion of the project, including data collection, labeling and documentation, laboratory preparations, model development, software integration, and testing processes.

### Equipment Providers
- Tetracam (MSC2-NIR8-1-A)
- Canon (EOS R50, EOS M50 Mark II)
- Fotric (323F Thermal Camera)
- AnalyzIR Software Suite

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-04 | Initial release for Zenodo submission |

---

**Last Updated:** February 4, 2026
