let selectedPoints = [];
        const video = document.getElementById('videoPlayer');
        const canvas = document.getElementById('canvasOverlay');
        const ctx = canvas.getContext('2d');
        const submitBtn = document.getElementById('submitBtn');
        const selectedPointsDiv = document.getElementById('selectedPoints');
        const clickInstructions = document.getElementById('clickInstructions');
        
        const instructionTexts = [
            "Click on the left edge of the hoop rim",
            "Click on the right edge of the hoop rim", 
            "Click on the center of the hoop"
        ];

        // Set canvas size to match video
        video.addEventListener('loadedmetadata', function() {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.style.width = '100%';
            canvas.style.height = 'auto';
        });

        // Handle canvas clicks
        canvas.addEventListener('click', function(e) {
            if (selectedPoints.length >= 2) return; // Don't allow more than 3 points
            
            const rect = canvas.getBoundingClientRect();
            const scaleX = canvas.width / rect.width;
            const scaleY = canvas.height / rect.height;
            
            const x = (e.clientX - rect.left) * scaleX;
            const y = (e.clientY - rect.top) * scaleY;
            
            const point = { x: Math.round(x), y: Math.round(y) };
            selectedPoints.push(point);
            
            // Draw point on canvas
            drawPoint(x, y, selectedPoints.length);
            
            // Update UI
            updateUI();
        });

        function drawPoint(x, y, pointNumber) {
            const colors = ['#ff4d4f', '#1890ff', '#52c41a']; // modern red, blue, green
            const color = colors[pointNumber - 1];

            ctx.strokeStyle = color;
            ctx.fillStyle = color;
            ctx.lineWidth = 1; // thinner lines

            const crosshairLength = 3; 
            const dotRadius = 2;      
            const fontSize = 8;        

            // Draw small crosshair
            ctx.beginPath();
            ctx.moveTo(x - crosshairLength, y);
            ctx.lineTo(x + crosshairLength, y);
            ctx.moveTo(x, y - crosshairLength);
            ctx.lineTo(x, y + crosshairLength);
            ctx.stroke();

            // Draw small filled dot
            ctx.beginPath();
            ctx.arc(x, y, dotRadius, 0, 2 * Math.PI);
            ctx.fill();

            // Draw point number label
            ctx.font = `${fontSize}px Segoe UI, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillStyle = '#fff';
            ctx.shadowColor = 'rgba(0,0,0,0.3)';
            ctx.shadowBlur = 2;
            ctx.fillText(pointNumber.toString(), x, y + 2);

            // Reset shadow
            ctx.shadowBlur = 0;
        }
        function updateUI() {
            const pointCount = selectedPoints.length;
            
            // Update selected points display
            selectedPointsDiv.style.display = 'block';
            for (let i = 0; i < pointCount; i++) {
                const pointDiv = document.getElementById(`point${i + 1}`);
                const coordsSpan = document.getElementById(`coords${i + 1}`);
                pointDiv.style.display = 'block';
                coordsSpan.textContent = `X: ${selectedPoints[i].x}, Y: ${selectedPoints[i].y}`;
            }
            
            // Update instructions
            if (pointCount < 2) {
                clickInstructions.innerHTML = `<strong>Step ${pointCount + 1}:</strong> ${instructionTexts[pointCount]}`;
            } else {
                clickInstructions.innerHTML = '<strong>All points selected!</strong> Click Submit to continue.';
                clickInstructions.style.backgroundColor = '#d4edda';
                clickInstructions.style.borderColor = '#28a745';
            }
            
            // Update submit button
            submitBtn.textContent = `Submit Hoop Location (${pointCount}/2 points selected)`;
            submitBtn.disabled = pointCount < 2;
        }

        
        // Optional: Add reset functionality
        document.addEventListener('keydown', function(e) {
            if (e.key === 'r' || e.key === 'R') {
                resetPoints();
            }
        });

        function resetPoints() {
            selectedPoints = [];
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            selectedPointsDiv.style.display = 'none';
            
            // Hide all point displays
            for (let i = 1; i <= 2; i++) {
                document.getElementById(`point${i}`).style.display = 'none';
            }
            
            // Reset instructions
            clickInstructions.innerHTML = `<strong>Step 1:</strong> ${instructionTexts[0]}`;
            clickInstructions.style.backgroundColor = '#e7f3ff';
            clickInstructions.style.borderColor = '#007cba';
            
            // Reset button
            submitBtn.textContent = 'Submit Hoop Location (0/2 points selected)';
            submitBtn.disabled = true;
        }

        // loading bar stuff
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
    //   const uploadForm = document.getElementById("upload-form");
    //   uploadForm.addEventListener("submit", async function(e) {

    //     e.preventDefault();
    //     const fileInput = document.getElementById("fileElem");
    //     const file = fileInput.files[0];
    //     if (!file) return;

    //     const formData = new FormData();
    //     formData.append("video", file);
    //     const aiToggle = document.getElementById("autoAiToggle").checked;
    //     if (aiToggle == true){
    //       const res = await fetch("/start-processing", {
    //         method: "POST",
    //         body: formData,
    //       });
    //       const data = await res.json();
    //       showProgressUI(data.session_id, data.project_name);
    //     }
    //     else {
    //       const res = await fetch("/start-processing", {
    //         method: "POST",
    //         body: formData,
    //       });
    //       const data = await res.json();
    //       window.location.href = `/select-hoop/${data.project_name}`
    //     }
    //     fileInput.value = ""; // clear the selected files to allow clean reuploading  
    //   });

      function submitHoopLocation() {
            if (selectedPoints.length < 2) {
                alert('Please select all 2 points first.');
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
            
            fetch(`/submit-hoop/${PROJECT_NAME}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    points: selectedPoints
                })
            })
            .then(response => response.json())
            .then(data => {
                 if (data.session_id) {
                    showProgressUI(data.session_id, data.project_name);
                } else {
                    alert('Error: ' + (data.error || 'Unknown error'));
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Submit Hoop Location (2/2 points selected)';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while submitting.');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Hoop Location (2/2 points selected)';
            });
        }
        // Add this function after your existing functions
function toggleVideoMode() {
    const video = document.getElementById('videoPlayer');
    const canvas = document.getElementById('canvasOverlay');
    
    if (video.style.pointerEvents === 'auto') {
        // Switch to selection mode
        video.style.pointerEvents = 'none';
        canvas.style.pointerEvents = 'all';
        canvas.style.cursor = 'crosshair';
        video.pause();
    } else {
        // Switch to video mode
        video.style.pointerEvents = 'auto';
        canvas.style.pointerEvents = 'none';
        canvas.style.cursor = 'default';
    }
}

// Add keyboard shortcut (add this after your existing keydown listener)
document.addEventListener('keydown', function(e) {
    if (e.key === 'r' || e.key === 'R') {
        resetPoints();
    }
    if (e.key === 'v' || e.key === 'V') {
        toggleVideoMode();
    }
});