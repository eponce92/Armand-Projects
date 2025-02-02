import imageSlider from './components/image-slider.js';

document.addEventListener('DOMContentLoaded', async function() {
  const form = document.getElementById('searchForm');
  const dropZone = document.getElementById('dropZone');
  const queryImage = document.getElementById('queryImage');
  const previewContainer = document.getElementById('previewContainer');
  const imagePreview = document.getElementById('imagePreview');
  const loading = document.getElementById('loading');
  const gallery = document.getElementById('gallery');
  const minScoreInput = document.getElementById('minScore');
  const minScoreValue = document.getElementById('minScoreValue');
  const batchSize = document.getElementById('batchSize');
  const browseFolderBtn = document.getElementById('browseFolderBtn');
  const folderPath = document.getElementById('folderPath');
  const imageModal = document.getElementById('imageModal');
  const modalImage = document.getElementById('modalImage');
  const modalClose = document.getElementById('modalClose');
  const searchTabs = document.querySelectorAll('.search-tab');
  const imageSearchSection = document.getElementById('imageSearchSection');
  const textSearchSection = document.getElementById('textSearchSection');
  const searchQuery = document.getElementById('searchQuery');

  let selectedImagePath = null;
  let currentSearchType = 'image';

  // Load last settings
  try {
    const response = await fetch('/last-settings');
    const settings = await response.json();
    if (settings && settings.last_folder) {
      folderPath.value = settings.last_folder;
    }
    if (settings && settings.last_query) {
      selectedImagePath = settings.last_query;
      imagePreview.src = `/image/${encodeURIComponent(settings.last_query)}`;
      previewContainer.style.display = 'block';
    }
    // Display last results if available
    if (settings && settings.last_results && settings.last_results.length > 0) {
      displayResults(settings.last_results);
    }
  } catch (error) {
    console.error('Error loading last settings:', error);
  }

  // Drag and drop handlers
  if (dropZone) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, unhighlight, false);
    });
  }

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight() {
    dropZone.classList.add('dragover');
  }

  function unhighlight() {
    dropZone.classList.remove('dragover');
  }

  // Click to select file
  dropZone.addEventListener('click', async () => {
    try {
      const response = await fetch('/select-image', {
        method: 'POST'
      });
      const data = await response.json();
      
      if (data.file_path) {
        selectedImagePath = data.file_path;
        folderPath.value = data.folder_path;
        imagePreview.src = `/image/${encodeURIComponent(data.file_path)}`;
        previewContainer.style.display = 'block';
      }
    } catch (error) {
      console.error('Error selecting image:', error);
    }
  });

  // Handle dropped files (optional, might not work with local files due to security)
  dropZone.addEventListener('drop', handleDrop, false);
  function handleDrop(e) {
    alert('Please use the click to select method for choosing images.');
    // Drag and drop won't work with local files due to security restrictions
  }

  // Update min score display with badge
  minScoreInput.addEventListener('input', function() {
    minScoreValue.textContent = `${this.value}%`;
  });

  // Folder selection handling
  browseFolderBtn.addEventListener('click', async () => {
    try {
      const response = await fetch('/select-image', {
        method: 'POST'
      });
      const data = await response.json();
      if (data.folder_path) {
        folderPath.value = data.folder_path;
      }
    } catch (error) {
      console.error('Error selecting folder:', error);
      alert('Error selecting folder: ' + error.message);
    }
  });

  // Update loading display functions with progress simulation
  let progressInterval;
  const searchProgress = document.getElementById('searchProgress');
  const progressText = document.getElementById('progressText');
  const statusText = document.getElementById('statusText');

  function showLoading() {
    // Reset progress
    updateProgress(0);
    loading.style.display = 'flex';
    setTimeout(() => loading.classList.add('show'), 10);
    
    // Start progress simulation
    let progress = 0;
    progressInterval = setInterval(() => {
      // Simulate progress up to 90%
      if (progress < 90) {
        progress += Math.random() * 15;
        progress = Math.min(progress, 90);
        updateProgress(progress);
      }
    }, 500);
  }

  function hideLoading() {
    // Complete progress animation
    clearInterval(progressInterval);
    updateProgress(100);
    
    // Hide loading overlay after a short delay
    setTimeout(() => {
      loading.classList.remove('show');
      setTimeout(() => {
        loading.style.display = 'none';
        // Reset progress for next time
        updateProgress(0);
      }, 300);
    }, 500);
  }

  function updateProgress(value) {
    const progress = Math.min(Math.max(value, 0), 100);
    searchProgress.style.width = `${progress}%`;
    progressText.textContent = `${Math.round(progress)}%`;
    
    // Update status text based on progress
    if (progress === 0) {
      statusText.textContent = 'Initializing search...';
    } else if (progress < 30) {
      statusText.textContent = 'Processing query...';
    } else if (progress < 60) {
      statusText.textContent = 'Searching for similar images...';
    } else if (progress < 90) {
      statusText.textContent = 'Analyzing results...';
    } else {
      statusText.textContent = 'Completing search...';
    }
  }

  // Update modal display functions
  function showModal(imagePath) {
    modalImage.src = `/image/${encodeURIComponent(imagePath)}`;
    imageModal.style.display = 'block';
    document.body.style.overflow = 'hidden';
    setTimeout(() => imageModal.classList.add('show'), 10);
  }

  function closeModal() {
    imageModal.classList.remove('show');
    setTimeout(() => {
      imageModal.style.display = 'none';
      document.body.style.overflow = '';
    }, 300);
  }

  // Handle search type switching
  searchTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const searchType = tab.dataset.searchType;
      if (searchType === currentSearchType) return;

      // Update tabs
      searchTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      // Update search button text
      const searchButton = form.querySelector('button[type="submit"]');
      searchButton.innerHTML = searchType === 'image' 
        ? '<i class="bi bi-search me-2"></i>Search Similar Images'
        : '<i class="bi bi-search me-2"></i>Search Images by Text';

      // Switch sections with animation
      if (searchType === 'image') {
        textSearchSection.classList.add('hidden');
        setTimeout(() => {
          textSearchSection.style.display = 'none';
          imageSearchSection.style.display = 'block';
          setTimeout(() => imageSearchSection.classList.remove('hidden'), 50);
        }, 300);
      } else {
        imageSearchSection.classList.add('hidden');
        setTimeout(() => {
          imageSearchSection.style.display = 'none';
          textSearchSection.style.display = 'block';
          setTimeout(() => textSearchSection.classList.remove('hidden'), 50);
        }, 300);
      }

      currentSearchType = searchType;
    });
  });

  // Form submission
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    gallery.innerHTML = '';
    showLoading();

    const formData = new FormData();
    formData.append('folder', folderPath.value);
    formData.append('min_score', minScoreInput.value / 100);
    formData.append('batch_size', batchSize.value);
    formData.append('search_type', currentSearchType);

    if (currentSearchType === 'image') {
      if (!selectedImagePath) {
        hideLoading();
        alert('Please select a query image!');
        return;
      }
      formData.append('query_path', selectedImagePath);
    } else {
      if (!searchQuery.value.trim()) {
        hideLoading();
        alert('Please enter a search query!');
        return;
      }
      formData.append('query_text', searchQuery.value.trim());
    }

    try {
      const response = await fetch('/search', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      if (!data.results || !Array.isArray(data.results)) {
        throw new Error('Invalid response format from server');
      }
      
      if (data.results.length === 0) {
        gallery.innerHTML = `
          <div class="no-results">
            <i class="bi bi-search" style="font-size: 3rem; opacity: 0.5;"></i>
            <h3>No matching images found</h3>
            <p>Try adjusting your search criteria or selecting a different folder.</p>
          </div>
        `;
      } else {
        displayResults(data.results);
      }
    } catch (error) {
      console.error('Error fetching search results:', error);
      gallery.innerHTML = `
        <div class="search-error">
          <i class="bi bi-exclamation-triangle" style="font-size: 3rem; color: var(--error-color);"></i>
          <h3>Error performing search</h3>
          <p>${error.message}</p>
          <button class="btn btn-outline-primary mt-3" onclick="location.reload()">
            <i class="bi bi-arrow-clockwise me-2"></i>Retry
          </button>
        </div>
      `;
    } finally {
      hideLoading();
    }
  });

  function displayResults(results) {
    if(results.length === 0) {
      gallery.innerHTML = '<div class="text-center p-5"><h3>No similar images found</h3></div>';
      return;
    }

    gallery.innerHTML = '';
    
    results.forEach((result, index) => {
      const item = document.createElement('div');
      item.className = 'gallery-item';
      
      // Determine size and aspect ratio classes
      const aspectRatio = result.height / result.width;
      
      // Add aspect ratio class first - simplified for better space usage
      if (aspectRatio > 1.3) {  // Very tall images
        item.classList.add('gallery-item--portrait');
      } else if (aspectRatio < 0.5) {  // Very wide images
        item.classList.add('gallery-item--panorama');
      } else if (aspectRatio < 0.7) {  // Moderately wide images
        item.classList.add('gallery-item--landscape');
      }
      
      // Add size class based on score - simplified
      if (result.score > 0.9) {
        item.classList.add('gallery-item--full');
      } else if (result.score > 0.8 && aspectRatio > 1.2) {
        item.classList.add('gallery-item--large');
      }
      
      const imageContainer = document.createElement('div');
      imageContainer.className = 'image-container';
      
      const img = document.createElement('img');
      img.src = `/image/${encodeURIComponent(result.path)}`;
      img.alt = result.filename;
      img.loading = 'lazy';
      
      const details = document.createElement('div');
      details.className = 'item__details';
      details.innerHTML = `
        <div class="details-content">
          <div class="details-header">
            <span class="match-number" title="${result.filename}">${result.filename}</span>
            <span class="match-score">${(result.score * 100).toFixed(1)}%</span>
          </div>
          <div class="match-description" title="${result.description}">
            ${result.description}
          </div>
        </div>
      `;
      
      imageContainer.appendChild(img);
      item.appendChild(imageContainer);
      item.appendChild(details);

      // Add click handler to view in slider
      item.addEventListener('click', () => {
        imageSlider.loadImages(results, index);
        imageSlider.show();
      });

      gallery.appendChild(item);
    });
  }

  // Modal handling
  imageModal.addEventListener('click', (e) => {
    if (e.target === imageModal) {
      closeModal();
    }
  });

  modalClose.addEventListener('click', closeModal);

  // Keyboard handling for modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && imageModal.style.display === 'block') {
      closeModal();
    }
  });
}); 