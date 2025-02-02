class ImageSlider {
  constructor() {
    console.log('Initializing ImageSlider');
    this.createSliderModal();
    this.slider = document.querySelector('.slider');
    console.log('Slider element:', this.slider);
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

    // Add click event delegation for preview images
    this.slider.addEventListener('click', (e) => {
      const previewItem = e.target.closest('.slider-item');
      if (previewItem && !previewItem.classList.contains('active')) {
        const items = Array.from(this.slider.children);
        const clickedIndex = items.indexOf(previewItem);
        if (clickedIndex > 0) {  // Only handle preview images (index > 0)
          this.goToImage(clickedIndex);
        }
      }
    });
  }

  loadImages(images, startIndex = 0) {
    this.images = images;
    this.currentIndex = startIndex;
    
    this.slider.innerHTML = images.map((img, index) => `
      <li class="slider-item" style="background-image: url('/image/${encodeURIComponent(img.path)}')">
        <div class="slider-content">
          ${img.description ? `
            <h2 class="title">${img.filename}</h2>
            <p class="description">${img.description}</p>
          ` : `
            <div class="match-score">Match Score: ${(img.score * 100).toFixed(1)}%</div>
          `}
        </div>
      </li>
    `).join('');

    // Reorder slides to show the clicked image
    if (startIndex > 0) {
      const items = Array.from(this.slider.children);
      for (let i = 0; i < startIndex; i++) {
        this.slider.appendChild(items[i]);
      }
    }

    // Update slides immediately
    requestAnimationFrame(() => {
      this.updateSlides();
    });
  }

  goToImage(index) {
    const items = Array.from(this.slider.children);
    const currentFirst = items[0];
    
    // Calculate how many positions to move
    const positions = index;
    
    // Move the required number of items to the end
    for (let i = 0; i < positions; i++) {
      const item = items[i];
      this.slider.appendChild(item);
    }
    
    // Update slides immediately after DOM change
    requestAnimationFrame(() => {
      this.updateSlides();
    });
  }

  show() {
    console.log('Showing slider modal');
    const modal = document.querySelector('.slider-modal');
    console.log('Modal element:', modal);
    modal.classList.add('active');
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
        item.classList.add('active');
        
        // Get container dimensions
        const containerWidth = window.innerWidth * 0.9;
        const containerHeight = window.innerHeight * 0.9;
        
        // Get image aspect ratio
        const imgAspectRatio = this.images[i].width / this.images[i].height;
        const containerAspectRatio = containerWidth / containerHeight;
        
        let width, height;
        if (imgAspectRatio > containerAspectRatio) {
          // Image is wider than container
          width = containerWidth;
          height = containerWidth / imgAspectRatio;
        } else {
          // Image is taller than container
          height = containerHeight;
          width = containerHeight * imgAspectRatio;
        }
        
        // Center the image
        item.style.width = `${width}px`;
        item.style.height = `${height}px`;
        item.style.position = 'absolute';
        item.style.left = '50%';
        item.style.top = '50%';
        item.style.transform = 'translate(-50%, -50%)';
        item.style.margin = '0';
        item.style.borderRadius = '2rem';
        item.style.boxShadow = 'var(--shadow)';
        item.style.opacity = '1';
        item.style.cursor = 'default';
        item.style.backgroundColor = 'var(--greyLight-1)';
      } else {
        // Preview images
        item.classList.remove('active');
        const rightPosition = i === 1 ? 'calc(44rem + 2rem)' :
                            i === 2 ? 'calc(22rem + 1rem)' :
                            i === 3 ? '2rem' : '-22rem';
        
        item.style.width = '20rem';
        item.style.height = '30rem';
        item.style.right = rightPosition;
        item.style.bottom = '2rem';
        item.style.top = 'auto';
        item.style.left = 'auto';
        item.style.transform = 'none';
        item.style.borderRadius = '1.6rem';
        item.style.boxShadow = 'var(--shadow)';
        item.style.opacity = i >= 4 ? '0' : '1';
        item.style.cursor = 'pointer';
        item.style.backgroundColor = 'var(--greyLight-1)';
      }
      
      // Re-enable transitions after a frame
      requestAnimationFrame(() => {
        item.style.transition = 'all 0.75s cubic-bezier(0.4, 0, 0.2, 1)';
      });
    });

    // Update content visibility
    items.forEach(item => {
      const content = item.querySelector('.slider-content');
      if (content) {
        content.style.display = 'block';
        content.style.opacity = '0';
      }
    });

    // Show content for the active (first) slide
    const activeContent = items[0].querySelector('.slider-content');
    if (activeContent) {
      activeContent.style.display = 'block';
      requestAnimationFrame(() => {
        activeContent.style.opacity = '1';
      });
    }
  }
}

// Initialize and export the slider
let imageSlider;

document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM loaded, initializing slider');
  imageSlider = new ImageSlider();
});

export default {
  loadImages: (...args) => imageSlider.loadImages(...args),
  show: () => imageSlider.show(),
  close: () => imageSlider.close(),
  prev: () => imageSlider.prev(),
  next: () => imageSlider.next()
}; 