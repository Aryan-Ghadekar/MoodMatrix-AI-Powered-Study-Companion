# MoodMatrix – AI-Powered Study Companion  

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![Framework](https://img.shields.io/badge/framework-FastAPI-009688?logo=fastapi&logoColor=white)
![Frontend](https://img.shields.io/badge/frontend-HTML%2FCSS%2FJS-orange?logo=javascript)
![AI](https://img.shields.io/badge/AI-DeepFace%20%7C%20MediaPipe%20%7C%20YOLO-yellow)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Jetson%20Nano-lightgrey)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-black?logo=github)](https://github.com/your-username/MoodMatrix)
![Status](https://img.shields.io/badge/status-Active-success)

MoodMatrix is an **AI-powered emotion-aware study companion** designed to optimize learning, improve focus, and support students with real-time emotional intelligence. It integrates AI with IoT hardware to create a personalized and distraction-free study environment.  

---

## Features  
- **Emotion-Aware Study Companion** – Detects and adapts to your emotional state during study sessions.  
- **AI Tutor for Discussion** – Ask questions, clarify doubts, and get real-time guidance.  
- **Distraction Monitor** – Tracks posture, facial cues, and audio signals to minimize distractions.  
- **Motivational Friend** – Encourages and boosts morale throughout study sessions.  
- **Dynamic Time-Table** – Creates adaptive schedules with priority-wise task execution.  
- **Emotional Stats Analyzer** – Generates insights and personalized timetables based on mood data.  

---

## Tech Stack  

### **Hardware**  
- Jetson Nano  
- High Quality Camera (for facial & posture recognition)  
- Speaker & Microphone (for interaction)  

### **Software**  
- FastAPI
- HTML, CSS, JS
- Python
- TensorFlow, PyTorch
- MediaPipe
- OpenCV
- Librosa
- Scikit-learn
- NumPy, Pandas 

---


##  Block Diagram - Proposed Architecture Diagram  
![alt text](assets/Proposed_System_Architecture.png)

##  Audio and Visual Cognitive Load Estimation Block Diagram  

<p align="center">
  <img src="assets/Audio_Cognitive_Load_Block_Diagram.png" alt="Audio Cognitive Load" width="40%" height="800px" style="margin-right:70px;"/>
  <img src="assets/Visual_Cognitive_Load_BlockDiagram1.png" alt="Visual Cognitive Load" width="40%" height="800px"/>
</p>


## Getting Started  

### 1. Clone the Repository  
```bash
git clone https://github.com/your-username/MoodMatrix-AI-Powered-Study-Companion.git
cd MoodMatrix-AI-Powered-Study-Companion
```


### 2. Set Up the Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`

pip install -r requirements.txt
```

### 3. Download Pre-trained Models
Download the required pre-trained models and place them in the `models/` directory.
- [Pose Landmarker Model](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker#models)
- [Face Landmarker Model](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker#models)

### 4. Run the Application
```bash
python backend/cognitive_load.py
```
# 🧩 PDF & PPT Conversion Setup Guide (Windows)

This guide helps you set up the dependencies required for PDF and PPT to image conversion in your Python project — **Poppler** (for PDFs) and **LibreOffice** (for PPTs).

---

## 📦 1. Install Poppler for Windows

Poppler is required for converting PDF files to images (used by libraries like `pdf2image`).

### 🪜 Steps

1. **Download Poppler**
   - Go to the official repository:  
     🔗 [https://github.com/oschwartz10612/poppler-windows/releases/](https://github.com/oschwartz10612/poppler-windows/releases/)
   - Download the latest `poppler-xx.x.x-x/Release-xx/` **ZIP file** (choose `poppler-xx.x.x-x/Release-64bit.zip` if you’re on a 64-bit system).

2. **Extract Files**
   - Extract the ZIP file (for example to):  
     ```
     C:\poppler
     ```

3. **Add Poppler to System PATH**
   - Press **Windows + S** → search **"Edit the system environment variables"**
   - Click **Environment Variables**
   - Under **System variables**, find and select **Path**, then click **Edit**
   - Click **New** → Add the following path:
     ```
     C:\poppler\Library\bin
     ```
   - Click **OK** to save all dialogs.

4. **Verify Installation**
   - Open **PowerShell** or **CMD** and run:
     ```bash
     pdftoppm -h
     ```
   - ✅ If installed correctly, it will show Poppler usage instructions.

---

## 🖥️ 2. Install LibreOffice

LibreOffice is required for converting PowerPoint (.ppt/.pptx) files to images or PDFs.

### 🪜 Steps

1. **Download LibreOffice**
   - Go to:  
     🔗 [https://www.libreoffice.org/download/download-libreoffice/](https://www.libreoffice.org/download/download-libreoffice/)

2. **Run Installer**
   - Choose the **Windows** version.
   - Install using default settings (it will install to `C:\Program Files\LibreOffice` by default).

3. **Add LibreOffice to PATH**
   - Press **Windows + S** → search **"Edit the system environment variables"**
   - Click **Environment Variables**
   - Under **System variables**, find **Path** → **Edit**
   - Add this path:
     ```
     C:\Program Files\LibreOffice\program
     ```

4. **Verify Installation**
   - Open CMD or PowerShell and run:
     ```bash
     soffice --version
     ```
   - ✅ If installed correctly, you’ll see LibreOffice version info.


