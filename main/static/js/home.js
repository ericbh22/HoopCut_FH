// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Carousel functionality
    const carousel = document.querySelector('.carousel');
    const prevButton = document.querySelector('.nav-prev');
    const nextButton = document.querySelector('.nav-next');
    let currentRotation = 0;
    
    function updateCarousel() {
        carousel.style.transform = `rotateY(${currentRotation}deg)`;
    }
    
    // Only add event listeners if elements exist
    if (nextButton) {
        nextButton.addEventListener('click', () => {
            currentRotation -= 120;
            updateCarousel();
        });
    }
    
    if (prevButton) {
        prevButton.addEventListener('click', () => {
            currentRotation += 120;
            updateCarousel();
        });
    }
    
    // Add keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft') {
            currentRotation += 120;
            updateCarousel();
        } else if (e.key === 'ArrowRight') {
            currentRotation -= 120;
            updateCarousel();
        }
    });
    
    // Load settings on page load
    loadSettings();
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
});

// Settings popup functionality
function toggleSettingsPopup() {
    const overlay = document.getElementById('overlay');
    const popup = document.getElementById("settingsPopup");
    
    if (overlay) overlay.classList.toggle('hidden');
    if (popup) popup.classList.toggle('hidden');
}
function toggleInfoPopup() {
            const overlay = document.getElementById('overlay2');
            const popup = document.getElementById('infoPopup');
            
            overlay.classList.toggle('hidden');
            popup.classList.toggle('hidden');
        }

// Load settings from server
async function loadSettings() {
    try {
        const response = await fetch("/get-settings");
        const settings = await response.json();
        
        // Set the toggle state based on server settings
        const autoAiToggle = document.getElementById("autoAiToggle");
        const threeToggle = document.getElementById("threePointToggle");
        
        if (autoAiToggle) autoAiToggle.checked = settings.auto_ai;
        if (threeToggle) {
            console.log(settings.three_point_adjust);
            threeToggle.checked = settings.three_point_adjust;
        }
    } catch (error) {
        console.error("Error loading settings:", error);
        // Default to true if loading fails
        const autoAiToggle = document.getElementById("autoAiToggle");
        const threeToggle = document.getElementById("threePointToggle");
        
        if (autoAiToggle) autoAiToggle.checked = true;
        if (threeToggle) threeToggle.checked = true;
    }
}

// Update Auto AI setting
function updateAutoAi() {
    const autoAiToggle = document.getElementById("autoAiToggle");
    if (!autoAiToggle) return;
    
    const isEnabled = autoAiToggle.checked;
    fetch("/toggle-auto-ai", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({enabled: isEnabled})
    })
    .then(res => res.json())
    .then(data => {
        console.log("Auto AI is now set to:", data.auto_ai);
    })
    .catch(error => {
        console.error("Error updating Auto AI setting:", error);
    });
}

// Update Three Point setting
function updateThree() {
    const threeToggle = document.getElementById("threePointToggle");
    if (!threeToggle) return;
    
    const isEnabled = threeToggle.checked;
    fetch("/toggle-three", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({enabled: isEnabled})
    })
    .then(res => res.json())
    .then(data => {
        console.log("update three is now set to:", data.three_point_adjust);
    })
    .catch(error => {
        console.error("Error updating Three Point setting:", error);
    });
}
