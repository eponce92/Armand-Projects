class ImageSlider {
  constructor() {
    this.createSliderModal();
    this.slider = document.querySelector('.slider');
    this.currentIndex = 0;
    this.images = [];
    this.setupEventListeners();
  }

  createSliderModal() {
    const modal = document.createElement('div');
    modal.className = 'slider-modal';
    modal.innerHTML = `
      <div class="slider-container">
        <button class="slider-close">×</button>
        <ul class="slider"></ul>
        <nav class="slider-nav">
          <button class="slider-btn prev">
            <ion-icon name="arrow-back-outline"></ion-icon>
          </button>
          <button class="slider-btn next">
            <ion-icon name="arrow-forward-outline"></ion-icon>
          </button>
        </nav>
      </div>
    `;
    document.body.appendChild(modal);
  }

  setupEventListeners() {
    document.querySelector('.slider-close').addEventListener('click', () => this.close());
    document.querySelector('.prev').addEventListener('click', () => this.prev());
    document.querySelector('.next').addEventListener('click', () => this.next());
    
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') this.close();
      if (e.key === 'ArrowLeft') this.prev();
      if (e.key === 'ArrowRight') this.next();
    });
  }

  loadImages(images, startIndex = 0) {
    // Reorder images array so that the clicked image becomes first
    const orderedImages = [...images.slice(startIndex), ...images.slice(0, startIndex)];
    this.images = orderedImages;
    
    this.slider.innerHTML = orderedImages.map((img, index) => `
      <li class="slider-item" style="background-image: url('/image/${encodeURIComponent(img.path)}')">
        <div class="slider-content">
          <div class="score">Match Score: ${(img.score * 100).toFixed(1)}%</div>
          <h2 class="title">${img.filename}</h2>
          <p class="description">${img.description}</p>
        </div>
      </li>
    `).join('');
  }

  show(startIndex = 0) {
    document.querySelector('.slider-modal').classList.add('active');
    document.body.style.overflow = 'hidden';
    this.updateSlides();
  }

  close() {
    document.querySelector('.slider-modal').classList.remove('active');
    document.body.style.overflow = '';
  }

  next() {
    const items = Array.from(this.slider.children);
    const firstItem = items[0];
    
    // Add transition class to first item
    firstItem.style.transition = 'all 0.75s cubic-bezier(0.4, 0, 0.2, 1)';
    
    // Move first item to the end
    this.slider.appendChild(firstItem);
    
    // Update positions immediately after DOM change
    requestAnimationFrame(() => {
      this.updateSlides();
    });
  }

  prev() {
    const items = Array.from(this.slider.children);
    const lastItem = items[items.length - 1];
    
    // Add transition class to last item
    lastItem.style.transition = 'all 0.75s cubic-bezier(0.4, 0, 0.2, 1)';
    
    // Move last item to the front
    this.slider.prepend(lastItem);
    
    // Update positions immediately after DOM change
    requestAnimationFrame(() => {
      this.updateSlides();
    });
  }

  updateSlides() {
    const items = Array.from(this.slider.children);
    
    items.forEach((item, i) => {
      // Reset transitions initially
      item.style.transition = 'none';
      
      if (i === 0) {
        // Main view image (active slide)
        item.style.width = '100%';
        item.style.height = '100%';
        item.style.top = '0';
        item.style.left = '0';
        item.style.right = 'auto';
        item.style.bottom = 'auto';
        item.style.transform = 'none';
        item.style.borderRadius = '0';
        item.style.boxShadow = 'none';
        item.style.opacity = '1';
      } else {
        // Preview images
        const rightPosition = i === 1 ? 'calc(440px + 2rem)' :
                            i === 2 ? 'calc(220px + 1rem)' :
                            i === 3 ? '2rem' : '-220px';
        
        item.style.width = '200px';
        item.style.height = '300px';
        item.style.right = rightPosition;
        item.style.bottom = '2rem';
        item.style.top = 'auto';
        item.style.left = 'auto';
        item.style.transform = 'none';
        item.style.borderRadius = '20px';
        item.style.boxShadow = '0 20px 30px rgba(255, 255, 255, 0.3) inset';
        item.style.opacity = i >= 4 ? '0' : '1';
      }
      
      // Re-enable transitions after a frame
      requestAnimationFrame(() => {
        item.style.transition = 'all 0.75s cubic-bezier(0.4, 0, 0.2, 1)';
      });
    });

    // Update content visibility
    items.forEach(item => {
      const content = item.querySelector('.slider-content');
      content.style.display = 'none';
      content.style.opacity = '0';
    });

    // Show content for the active (first) slide
    const activeContent = items[0].querySelector('.slider-content');
    activeContent.style.display = 'block';
    requestAnimationFrame(() => {
      activeContent.style.opacity = '1';
    });
  }
}

// Initialize and export the slider
const imageSlider = new ImageSlider();
export default imageSlider; 