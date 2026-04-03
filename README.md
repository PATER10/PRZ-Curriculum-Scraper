# 🎓 PRZ Curriculum Scraper

An automated data extraction tool designed specifically for the **Rzeszow University of Technology** study plan system. This script crawls the university's academic portal to transform messy HTML tables into structured data for developers and students.

## 📖 Overview

The **PRZ Curriculum Scraper** is a specialized Python utility that navigates the complex structure of the PRZ "Krk" system. It doesn't just list subject names; it dives deep into each course card to extract the actual **syllabus topics** (TK) taught during lectures and laboratories.

## ✨ Key Features

* **Deep Subject Scraping**: Automatically follows links to individual course cards to fetch detailed knowledge points.
* **Smart Categorization**: Handles common exceptions like foreign languages and elective modules.
* **Visual Organization**: Assigns unique HEX color codes to subjects for easier UI implementation in calendars or charts.
* **Multi-Format Export**: Generates both **JSON** (for apps) and **CSV** (for Excel/Data Science) files.
* **UUID Based**: Every subject and knowledge point is assigned a unique `uuid4` string, making it database-ready out of the box.

---

## 🛠️ Technical Workflow

1.  **Request**: The script fetches the study plan HTML based on a specific URL.
2.  **Parse**: Using `BeautifulSoup`, it identifies the "Analiza" table containing the semester schedule.
3.  **Traverse**: For every valid subject, it visits the sub-page (`karta.pl`) to scrape the "Program Content" (TK codes).
4.  **Clean**: Whitespace is normalized, and TK codes are converted into numerical order.
5.  **Export**: Data is saved into the `prefix_subjects` and `prefix_knowledge_points` files.

---

## 🚀 Getting Started

### Prerequisites
Make sure you have Python 3.x installed and the following libraries:
```bash
pip install requests beautifulsoup4 pandas