# CLIP Image Search 🔍

A modern web application that uses OpenAI's CLIP model to find visually similar images in your local folders. Built with FastAPI and modern web technologies.

## ✨ Features

- 🎯 AI-powered visual similarity search using CLIP
- 🖼️ Modern, responsive gallery with masonry layout
- 🎨 Professional UI with glass morphism effects
- 🔄 Real-time image preview and batch processing
- 📊 Adjustable similarity threshold with visual feedback
- 🎛️ Customizable batch size for performance
- 📱 Fully responsive design
- ⌨️ Keyboard navigation support
- 🖱️ Drag and drop support
- 🔍 Image content analysis
- 💾 Session persistence

## 🎨 UI Features

- Modern glass morphism design
- Smooth animations and transitions
- Interactive slider controls
- Professional color scheme
- Responsive image gallery
- Immersive image viewer
- Loading states and feedback
- Native folder picker integration

## 🛠️ Technology Stack

### Frontend

- HTML5 & CSS3
- Modern JavaScript (ES6+)
- Bootstrap 5
- Masonry.js for gallery layout
- IonIcons for icons
- Custom animations and transitions

### Backend

- FastAPI
- Python 3.8+
- OpenAI CLIP model
- PIL for image processing
- TorchVision
- Async processing

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser
- CUDA-capable GPU (recommended)

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

## 💡 Usage

1. **Select Query Image**

   - Click or drag an image to the upload area
   - Preview appears automatically

2. **Choose Search Location**

   - Use the "Browse" button to select a folder
   - All supported image formats will be searched

3. **Adjust Settings**

   - Set minimum similarity score (0.0 - 1.0)
   - Choose batch size based on your hardware
   - Larger batch sizes are faster but use more memory

4. **View Results**
   - Results appear in a responsive gallery
   - Sorted by similarity score
   - Click any image for full-screen view
   - Use arrow keys to navigate in full-screen mode

## 🗂️ Project Structure

```
clip-image-search/
├── backend/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   └── clip_utils.py     # CLIP model utilities
├── frontend/
│   ├── components/       # Modular UI components
│   ├── index.html       # Main HTML
│   ├── script.js        # Main JavaScript
│   └── styles.css       # Main styles
├── requirements.txt
├── .gitignore
└── README.md
```

## ⚙️ Configuration

The application can be configured through several parameters:

- **Batch Size**:

  - Small (16 images)
  - Medium (32 images) - default
  - Large (64 images)

- **Similarity Score**:
  - Range: 0.0 to 1.0
  - Default: 0.2
  - Higher values = stricter matching

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m '✨ Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for the CLIP model
- FastAPI team
- Bootstrap team
- Masonry.js contributors
- IonIcons team
