// static/script.js
let dropArea = document.getElementById('drop-area')
let fileInput = document.getElementById('fileElem')
let preview = document.getElementById('preview');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
  dropArea.addEventListener(eventName, preventDefaults, false)
})

function preventDefaults(e) {
  e.preventDefault()
  e.stopPropagation()
}

;['dragenter', 'dragover'].forEach(eventName => {
  dropArea.classList.add('highlight')
})

;['dragleave', 'drop'].forEach(eventName => {
  dropArea.classList.remove('highlight')
})

dropArea.addEventListener('drop', handleDrop, false)

function handleDrop(e) {
  let dt = e.dataTransfer
  let files = dt.files
  if (files.length > 0) {
    fileInput.files = files
    previewFile(files[0])
  }
}


document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("fileElem");

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      previewFile(fileInput.files[0]);
    }
  });

  // (Optional) Add this if not already present
  const dropArea = document.getElementById("drop-area");
  ["dragenter", "dragover", "dragleave", "drop"].forEach(event => {
    dropArea.addEventListener(event, e => {
      e.preventDefault();
      e.stopPropagation();
    });
  });

  dropArea.addEventListener("drop", e => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      fileInput.files = files; // assign to input
      previewFile(files[0]);
    }
  });
});

function toggleInfoPopup() {
            const overlay = document.getElementById('overlay2');
            const popup = document.getElementById('infoPopup');
            
            overlay.classList.toggle('hidden');
            popup.classList.toggle('hidden');
        }


function previewFile(file) {
  let reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onloadend = function () {
    preview.src = reader.result;
    preview.style.display = 'block';
    const startBtn = document.getElementById('start-editing-btn');
    if (startBtn) {
      startBtn.style.display = 'inline-block';
    }
  };
}

window.addEventListener('pageshow', function (event) {
  if (event.persisted || performance.getEntriesByType("navigation")[0].type === "back_forward") {
    window.location.reload(); // force a fresh reload
  }
  });
    // Search functionality
    let searchVisible = false;
    
    function toggleSearch() {
      const searchContainer = document.getElementById('searchContainer');
      const headerContent = document.getElementById('headerContent');
      const searchInput = document.getElementById('searchInput');
      
      searchVisible = !searchVisible;
      
      if (searchVisible) {
        // Hide header content and show search
        headerContent.classList.add('hidden');
        setTimeout(() => {
          searchContainer.classList.add('active');
          setTimeout(() => searchInput.focus(), 100);
        }, 200); // timeout to allow animation to play  this is basically saying was 0.2 seconds, then do change it to active ( trigering animation) and then wait 0.1 seconds to allow that animation to finish
      } else {
        // Hide search and show header content
        searchContainer.classList.remove('active');
        setTimeout(() => {
          headerContent.classList.remove('hidden');
        }, 200);  // defines a function , kinda like lambda and calls it 200 ms later 
        searchInput.value = '';
        clearSearch();
      }
    }
    
    function clearSearch() {
      const searchInput = document.getElementById('searchInput');
      const clearBtn = document.getElementById('clearSearch');
      
      searchInput.value = '';
      clearBtn.classList.remove('visible');
      filterProjects('');
    }
    
    function filterProjects(query) {
      const videoList = document.getElementById('videoList');
      const noResults = document.getElementById('noResults');
      const items = videoList.querySelectorAll('li[data-project-name]'); // this means select all li elements, so ignore div elements 
      
      let visibleCount = 0; 
      
      items.forEach(item => {
        const projectName = item.getAttribute('data-project-name');
        const matches = projectName.includes(query.toLowerCase());
        
        if (matches || query === '') {
          item.classList.remove('hidden');
          visibleCount++; // make one visible and remove the hidden tag if our query is nothing 
          
          // Add highlight effect for search matches
          if (query !== '' && matches) { // if the query isnt empty and there are matches 
            item.classList.add('highlight'); // add  a highlight class onto them for styling if there is a match 
          } else {
            item.classList.remove('highlight'); // otherwise this means we didnt have a match, we just had empty query, dont add the highlight class on 
          }
        } else {
          item.classList.add('hidden');  // otehrwise make it hidden 
          item.classList.remove('highlight'); 
        }
      });
      
      // Show/hide no results message
      if (visibleCount === 0 && query !== '') {
        noResults.classList.add('visible'); 
      } else {
        noResults.classList.remove('visible');
      } 
    }
    
    // Search input event listeners
    document.addEventListener('DOMContentLoaded', function() {
      const searchInput = document.getElementById('searchInput');
      const clearBtn = document.getElementById('clearSearch');
      
      searchInput.addEventListener('input', function() { // listening for an input event like a lambda 
        const query = this.value.trim();
        filterProjects(query); 
        
      });
      
      // ESC key to close search
      document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && searchVisible) {
          toggleSearch();
        }
      });
    });
    document.addEventListener('click', function(e) {
        if (searchVisible) {
          const searchContainer = document.getElementById('searchContainer');
          const searchToggle = document.querySelector('.search-toggle');
          
          // Check if click is outside search container and not on search toggle
          if (!searchContainer.contains(e.target) && !searchToggle.contains(e.target)) {
            toggleSearch();
          }
        }
      });

    // Delete project function
    function deleteProject(projectName, event) {
      event.preventDefault();
      event.stopPropagation(); // dont propogate changes  everywhere 
      
      if (confirm(`Are you sure you want to delete "${projectName}"? This action cannot be undone.`)) {
        // Show loading state
        const deleteBtn = event.target;
        const originalText = deleteBtn.innerHTML;
        deleteBtn.innerHTML = '⏳';
        deleteBtn.disabled = true;
        
        // Make request to Flask backend
        fetch('/delete_project', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            project_name: projectName
          })
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            // Animate out the deleted item
            const listItem = deleteBtn.closest('li');
            listItem.style.transition = 'all 0.3s ease';
            listItem.style.transform = 'translateX(-100%)';
            listItem.style.opacity = '0';
            
            // Remove from DOM after animation
            setTimeout(() => {
              listItem.remove();
              
              // Check if no projects left
              const remainingItems = document.querySelectorAll('#videoList li[data-project-name]');
              if (remainingItems.length === 0) {
                document.getElementById('videoList').innerHTML = '<li>No past projects yet.</li>';
              }
            }, 300);
            
            // Show success message (you can customize this)
            console.log('Project deleted successfully');
          } else {
            // Show error message
            alert('Error deleting project: ' + (data.error || 'Unknown error'));
            deleteBtn.innerHTML = originalText;
            deleteBtn.disabled = false;
          }
        })
        .catch(error => {
          console.error('Error:', error);
          alert('Error deleting project. Please try again.');
          deleteBtn.innerHTML = originalText;
          deleteBtn.disabled = false;
        });
      }
    }
    function toggleSettingsPopup(){
      console.log("entering")
      const overlay = document.getElementById('overlay');
      overlay.classList.toggle('hidden');
        const popup = document.getElementById("settingsPopup");
        popup.classList.toggle("hidden");
    }
        async function loadSettings() {
            try {
                const response = await fetch("/get-settings");
                const settings = await response.json();
                
                // Set the toggle state based on server settings
                const autoAiToggle = document.getElementById("autoAiToggle");
                autoAiToggle.checked = settings.auto_ai;
                const threeToggle = document.getElementById("threePointToggle")
                console.log(settings.three_point_adjust)
                threeToggle.checked = settings.three_point_adjust
            } catch (error) {
                console.error("Error loading settings:", error);
                // Default to true if loading fails
                document.getElementById("autoAiToggle").checked = true;
                document.getElementById("threePointToggle").checked = true;
            }
        }
    function updateAutoAi(){
      const isEnabled = document.getElementById("autoAiToggle").checked;
      fetch("/toggle-auto-ai", {
        method: "POST",
        headers: {"Content-Type": "application/json" },
        body: JSON.stringify({enabled: isEnabled})
      })
      .then(res => res.json()) // res os actually not useful here apart from error debugging 
      .then(data => {
    // Print the result to console for debugging
          console.log("Auto AI is now set to:", data.auto_ai);
        })
        .catch(error => {
          console.error("Error updating Auto AI setting:", error);
        });
    }
    function updateThree(){
        const isEnabled = document.getElementById("threePointToggle").checked;
        fetch("/toggle-three",{
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({enabled: isEnabled})
        })
        .then(res => res.json()) // res os actually not useful here apart from error debugging 
        .then(data => {
        // Print the result to console for debugging
            console.log("update three is now set to:", data.auto_ai);
            })
            .catch(error => {
            console.error("Error updating Auto AI setting:", error);
            });
    }
    window.addEventListener('DOMContentLoaded', loadSettings);


      // Progress UI box
      function showProgressUI(sessionId, projectName) {
        const overlay = document.createElement('div');
        overlay.id = 'progressOverlay';
        overlay.innerHTML = `
          <div class="progress-box">
            <h3>Processing ${projectName}...</h3>
            <p id="progressStage">Initializing...</p>
            <div class="progress-bar">
              <div class="progress-bar-fill" id="progressFill" style="width: 0%"></div>
            </div>
          </div>
        `;
        document.body.appendChild(overlay);

        const source = new EventSource(`/progress-stream/${sessionId}`);
        source.onmessage = (event) => {
          const data = JSON.parse(event.data);
          if (data.error) {
            document.getElementById("progressStage").textContent = "Error: " + data.error;
            source.close();
          } else if (data.is_complete) {
            document.getElementById("progressStage").textContent = "Complete!";
            document.getElementById("progressFill").style.width = "100%";
            source.close();
            setTimeout(() => {
              window.location.href = "/projects/" + projectName;
            }, 1000);
          } else {
            document.getElementById("progressStage").textContent = data.stage;
            document.getElementById("progressFill").style.width = `${data.progress}%`;
          }
        };
      }

      // Hook into form submission
      const uploadForm = document.getElementById("upload-form");
      uploadForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        const fileInput = document.getElementById("fileElem");
        const file = fileInput.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append("video", file);
        const aiToggle = document.getElementById("autoAiToggle").checked;
        if (aiToggle == true){
          const res = await fetch("/start-processing", {
            method: "POST",
            body: formData,
          });
          const data = await res.json();
          showProgressUI(data.session_id, data.project_name);
        }
        else {
          const res = await fetch("/start-processing", {
            method: "POST",
            body: formData,
          });
          const data = await res.json();
          window.location.href = `/select-hoop/${data.project_name}`
        }
        fileInput.value = ""; // clear the selected files to allow clean reuploading  
      });
      function deleteAll(event) {
        event.preventDefault();
        event.stopPropagation();

        if (!confirm("Are you sure you want to delete all projects? This action cannot be undone.")) return;

        const items = document.querySelectorAll('#videoList li[data-project-name]');
        if (items.length === 0) return;

        items.forEach((item) => {
          const projectName = item.getAttribute('data-project-name');

          fetch('/delete_project', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ project_name: projectName })
          })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              item.style.transition = 'all 0.3s ease';
              item.style.transform = 'translateX(-100%)';
              item.style.opacity = '0';
              setTimeout(() => {
                item.remove();
                const remainingItems = document.querySelectorAll('#videoList li[data-project-name]');
                if (remainingItems.length === 0) {
                  document.getElementById('videoList').innerHTML = '<li>No past projects yet.</li>';
                }
              }, 300);
            } else {
              console.error("Failed to delete:", projectName);
            }
          })
          .catch(err => {
            console.error("Error deleting project:", err);
          });
        });
      }
      