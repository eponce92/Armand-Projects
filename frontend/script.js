document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('searchForm');
  const dropZone = document.getElementById('dropZone');
  const queryImage = document.getElementById('queryImage');
  const previewContainer = document.getElementById('previewContainer');
  const imagePreview = document.getElementById('imagePreview');
  const loading = document.getElementById('loading');
  const gallery = document.getElementById('gallery');
  const progress = document.querySelector('.progress');
  const progressBar = progress.querySelector('.progress-bar');
  const minScoreInput = document.getElementById('minScore');
  const minScoreValue = document.getElementById('minScoreValue');
  const batchSize = document.getElementById('batchSize');
  const folderInput = document.getElementById('folderInput');
  const browseFolderBtn = document.getElementById('browseFolderBtn');
  const imageModal = document.getElementById('imageModal');
  const modalImage = document.getElementById('modalImage');
  const modalClose = document.getElementById('modalClose');

  // Initialize Masonry with proper options
  let msnry = new Masonry(gallery, {
    itemSelector: '.gallery-item',
    columnWidth: '.gallery-item',
    percentPosition: true,
    gutter: 24,
    transitionDuration: '0.3s',
    initLayout: true,
    fitWidth: false
  });

  // Drag and drop handlers
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
  });

  function highlight() {
    dropZone.classList.add('dragover');
  }

  function unhighlight() {
    dropZone.classList.remove('dragover');
  }

  // Handle dropped files
  dropZone.addEventListener('drop', handleDrop, false);
  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    queryImage.files = files;
    handleFiles(files);
  }

  // Click to select file
  dropZone.addEventListener('click', () => queryImage.click());
  queryImage.addEventListener('change', () => handleFiles(queryImage.files));

  // Handle selected files
  function handleFiles(files) {
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
          imagePreview.src = e.target.result;
          previewContainer.style.display = 'block';
        }
        reader.readAsDataURL(file);
      }
    }
  }

  // Update min score display with badge
  minScoreInput.addEventListener('input', function() {
    minScoreValue.textContent = this.value;
  });

  // Folder selection handling
  browseFolderBtn.addEventListener('click', async () => {
    try {
      const response = await fetch('/select-folder');
      const data = await response.json();
      if (data.folder_path) {
        document.getElementById('folderPath').value = data.folder_path;
      }
    } catch (error) {
      console.error('Error selecting folder:', error);
      alert('Error selecting folder: ' + error.message);
    }
  });

  // Form submission
  form.addEventListener('submit', async function(e) {
    e.preventDefault();
    gallery.innerHTML = '';
    loading.style.display = 'flex';  // Changed to flex for centering

    const queryImageInput = document.getElementById('queryImage');
    const folderPathInput = document.getElementById('folderPath');

    if(queryImageInput.files.length === 0) {
      alert('Please select a query image!');
      loading.style.display = 'none';
      return;
    }

    const formData = new FormData();
    formData.append('query', queryImageInput.files[0]);
    formData.append('folder', folderPathInput.value);
    formData.append('min_score', minScoreInput.value);
    formData.append('batch_size', batchSize.value);

    try {
      const response = await fetch('/search', {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      displayResults(data.results);
    } catch (error) {
      console.error('Error fetching search results:', error);
      alert('Error fetching search results: ' + error.message);
    } finally {
      loading.style.display = 'none';
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
      
      const card = document.createElement('div');
      card.className = 'position-relative';
      
      const img = document.createElement('img');
      img.src = result.thumbnail;
      img.className = 'img-fluid';
      img.alt = `Similar image ${index + 1}`;
      img.loading = 'lazy';
      
      const score = document.createElement('div');
      score.className = 'score-badge';
      score.textContent = `${(result.score * 100).toFixed(1)}%`;
      
      card.appendChild(img);
      card.appendChild(score);
      item.appendChild(card);
      gallery.appendChild(item);

      // Add click handler to view full image
      card.addEventListener('click', () => {
        modalImage.src = result.path;
        imageModal.style.display = 'block';
        document.body.style.overflow = 'hidden';  // Prevent scrolling when modal is open
      });
      
      // Update masonry layout when image loads
      img.onload = () => {
        msnry.layout();
      };
    });

    // Initialize layout after all images are added
    msnry.layout();
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

  function closeModal() {
    imageModal.style.display = 'none';
    document.body.style.overflow = '';  // Restore scrolling
  }

  // Handle window resize for masonry layout
  let resizeTimeout;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
      msnry.layout();
    }, 100);
  });
}); 