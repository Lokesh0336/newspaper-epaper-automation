# Newspaper E-Paper Automation

<p align="center">
  <img src="assets/hero.png" alt="Newspaper E-Paper Automation" width="900">
</p>

<p align="center">
  <strong>Automate e-paper page capture and generate high-quality PDF documents.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#supported-newspapers">Supported Newspapers</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#roadmap">Roadmap</a>
</p>

<p align="center">

![Version](https://img.shields.io/badge/version-v1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Status](https://img.shields.io/badge/status-active-success)
![Open Source](https://img.shields.io/badge/open%20source-yes-black)

</p>

---

## Overview

**Newspaper E-Paper Automation** is an open-source Python project designed to automate the process of accessing newspaper e-paper pages, capturing individual pages, and generating high-quality PDF documents.

The project is built with a modular architecture where each newspaper has its own independent automation implementation.

This approach makes it easier to maintain existing integrations and add support for new newspapers without unnecessarily affecting other integrations.

---

## Supported Newspapers

### Currently Available

| Newspaper | Integration |
|-----------|-------------|
| **Eenadu** | ✅ Available |
| **Sakshi** | ✅ Available |

### Coming Soon

Additional newspaper integrations will be added in future releases.

Planned and potential integrations include:

- Andhra Jyothi
- Namasthe Telangana
- Additional regional newspapers
- Additional newspaper editions
- More language support

> **Note:** Newspaper integrations are developed and tested individually because different e-paper platforms can use different page structures, navigation systems, and access mechanisms.

---

# Features

- 📅 Date-based e-paper access
- 🌐 Browser-based automation
- 🔄 Automated page navigation
- 📸 High-resolution page capture
- 📄 High-quality PDF generation
- 🧩 Independent newspaper integrations
- 🛠️ Modular architecture
- 💻 Command-line execution
- 🌍 Designed for future newspaper and language support
- 🔓 Open-source MIT License
- 🤝 Open to developer contributions

---

# Technology Stack

The project currently uses:

| Technology | Purpose |
|------------|---------|
| **Python** | Core automation |
| **Selenium** | Browser automation |
| **Undetected ChromeDriver** | Chrome automation |
| **Pillow** | Image processing and PDF generation |
| **Google Chrome** | E-paper browser automation |

---

# Requirements

Before using the project, install:

- Python 3.10 or later
- Google Chrome
- Internet connection

Verify Python:

```bash
python --version
