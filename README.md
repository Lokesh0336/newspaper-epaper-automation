# Newspaper E-Paper Automation

<div align="center">

**Automate e-paper page capture and high-quality PDF generation.**

[![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)](https://github.com/Lokesh0336/newspaper-epaper-automation)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GitHub](https://img.shields.io/badge/GitHub-Open%20Source-black.svg)](https://github.com/Lokesh0336/newspaper-epaper-automation)

</div>

---

## Overview

**Newspaper E-Paper Automation** is an open-source Python project for automating the process of capturing newspaper e-paper pages and generating high-quality PDF documents.

The project uses browser automation to navigate e-paper pages, capture individual pages, and convert the captured pages into PDF files.

Each newspaper is maintained as an independent integration, making the project easier to maintain and extend as additional newspapers are added.

---

## Currently Supported

The project currently supports:

- **Eenadu**
- **Sakshi**

Additional newspapers and editions will be added in future releases.

### Planned Integrations

Potential future integrations include:

- Andhra Jyothi
- Namasthe Telangana
- Additional regional newspapers
- Additional newspaper editions

The availability of each integration depends on the structure and accessibility of the respective e-paper website.

---

## Features

- Automated e-paper page navigation
- Date-based newspaper access
- High-resolution page screenshots
- Automatic page capture
- Newspaper-specific automation
- PDF generation from captured pages
- Modular project structure
- Command-line execution
- Local browser profile support
- Support for adding additional newspapers
- Open-source under the MIT License

---

## Technology Stack

The project is built using:

- **Python**
- **Selenium**
- **Undetected ChromeDriver**
- **Pillow**
- **Google Chrome**

---

## Requirements

Before using the project, install the following:

- Python 3.10 or later
- Google Chrome
- Internet connection

Check your Python installation:

```bash
python --version
