# CLIP Image Search 🔍

A modern web application that uses OpenAI's CLIP model to find visually similar images in your local folders. Built with FastAPI and modern web technologies.

## ✨ Features

- 🖼️ Drag-and-drop image upload
- 📁 Native folder picker integration
- 🔍 AI-powered visual similarity search
- 📊 Adjustable similarity threshold
- 🎯 Batch processing control
- 🖥️ Modern, responsive UI
- 🚀 Real-time results with progress indication

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Model**: OpenAI CLIP
- **UI Framework**: Bootstrap 5
- **Layout**: Masonry.js

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/clip-image-search.git
   cd clip-image-search
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the server:

   ```bash
   uvicorn backend.main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## 🎯 Usage

1. Click or drag an image into the upload area
2. Use the "Browse" button to select a folder to search in
3. Adjust the minimum similarity score if needed
4. Choose a batch size based on your system's capabilities
5. Click "Search Similar Images" to start the search
6. Click on any result to view it in full size

## 📁 Project Structure

```
clip-image-search/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   └── clip_utils.py
├── frontend/
│   ├── index.html
│   └── script.js
├── temp/
│   └── thumbnails/
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Configuration

- Adjust batch size in the UI based on your system's memory
- Minimum similarity score can be set between 0 and 1
- Temporary files are stored in the `temp` directory

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m '✨ Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for the CLIP model
- FastAPI team for the amazing framework
- Bootstrap team for the UI framework
- David DeSandro for Masonry.js
