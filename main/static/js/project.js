document.addEventListener("DOMContentLoaded", () => {
  const project = document.body.dataset.project;

  document.querySelectorAll(".clip-card").forEach(card => {
    const makeBtn = card.querySelector(".make-btn");
    const missBtn = card.querySelector(".miss-btn");
    

    makeBtn.addEventListener("click", () => {
      const filename = card.dataset.filename; // make sure we are getting the updated file name consistently 
      updateLabel(filename, "make", project);
      makeBtn.classList.add("active");
      missBtn.classList.remove("active");
    });

    missBtn.addEventListener("click", () => {
      const filename = card.dataset.filename;
      updateLabel(filename, "miss", project);
      missBtn.classList.add("active");
      makeBtn.classList.remove("active");
    });
  });
});

function updateLabel(filename, newLabel, project) {
  fetch(`/relabel`, { // does a post request to flask relabel endpoint 
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, newLabel, project }),
  }).then(async res => { // once the response is received
    if (res.ok) {  // if the res is ok 
      const data = await res.json();  // grab the data 
      const newFilename = data.newFilename; // grab the NEW FILE NAME, this is returned by my json, this is basically the res, which we got and named data 
      // Update the DOM
      const card = document.querySelector(`.clip-card[data-filename="${filename}"]`); //find the card being controlled, this is the outdated card name 
      if (card) {
        card.dataset.filename = newFilename; // if that card exists, which it should 

        // Update <video> source
        const source = card.querySelector("video source"); // finds the first source inside video, this is standard css / js syntax
        source.src = `/projects/${project}/clips/${newFilename}`; // update the src to our new file 
        //card.querySelector("video").load(); // buffer the new video, forces it to show again, not needed since our video wont change 
        // Update download button
        const dlBtn = card.querySelector(".download-btn"); // select the download button and set its onclick attribute to download a different clip, keep in mind the orighanl onclick was  "downloadClip('{{ clip }}', '{{ project }}' 
        dlBtn.setAttribute("onclick", `downloadClip('${newFilename}', '${project}')`);

        // Update button states (optional visual feedback)
        const makeBtn = card.querySelector(".make-btn");
        const missBtn = card.querySelector(".miss-btn");
        if (newLabel === "make") {
          makeBtn.classList.add("active");
          missBtn.classList.remove("active"); // cahgning colours 
        } else {
          missBtn.classList.add("active");
          makeBtn.classList.remove("active");
        }
      }
    } else {
      const err = await res.json();
      alert("Failed to update label: " + err.error);
    }
  });
}

function toggleInfoPopup() {
            const overlay = document.getElementById('overlay2');
            const popup = document.getElementById('infoPopup');
            
            overlay.classList.toggle('hidden');
            popup.classList.toggle('hidden');
        }
function downloadClip(filename, project) {
  const url = `/projects/${project}/clips/${filename}`;
  const a = document.createElement('a');
  a.href = url;
  a.download = filename; // browser hint to download instead of navigating
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

function downloadAll() {
  const project = document.body.dataset.project;
  console.log(project)
  window.location.href = `/download-all/${project}`; // safer with zip files in case browser limits 
}

function downloadPlots(){
  const project = document.body.dataset.project;
  console.log(project)
  window.location.href = `/download-all-plots/${project}`
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
