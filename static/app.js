const { createApp } = Vue;

// Main function to update chart
function drawChartFrom(dataList) {
    const x = dataList.map(item => item.timestamp);
    const y = dataList.map(item => item.value);

    // Setting for Plotly.js
    Plotly.newPlot('chart', [{
        x: x,
        y: y,
        mode: 'lines+markers',
        type: 'scatter',
        marker: { size: 8 }
    }], {
        title: 'Resistance vs Time',
        xaxis: { title: 'Timestamp' },
        yaxis: { title: 'Value' }
    });
}
const app = createApp({
    data() {
        return {
            imageList: [],
            currentImageIndex: null,
            newTimestamp: '',
            newValue: null,
            dataList: [
                {timestamp: '2025-05-02 8', value: 17}, // Test data points
                {timestamp: '2025-05-02 12:45', value: 13},
                {timestamp: '2025-05-02 14:33', value: 22},
                {timestamp: '2025-05-03', value: 51}
            ],
            selectedFile: '',
            historyFiles: [],
        }
    },
    // All methods of calling data
    methods: {
        updateChartFromEdit() { // Call itself
            drawChartFrom(this.dataList);
        },

        // Function grab data from OCR script
        async updateChartFromLive() {
            try {
                const response = await fetch('/realtime_data');
                const data = await response.json();
                drawChartFrom(data);
            } catch (error) {
                alert("Not able to access data:" + error.message);
            }
        },
        // Save exits data in the data sheet
        async saveCurrentData() {
            try {
                const response = await fetch('/save_data', {
                    method: 'POST',
                    headers: {'content-Type': 'application/json'},
                    body: JSON.stringify(this.dataList)
                });
                const result = await response.json();
                if (result.status === "success") {
                    alert("Saved as: " + result.filename);
                    this.loadHistoryFiles();
                } else {
                    alert("Error: " + result.message);
                }
            } catch (err) {
                alert("Save failed: " + err.message);
            }
        },
        // Region: Upper button Section; Select Window
        async loadHistoryFiles() {
            try {
                const response = await fetch('/list_history');
                const files = await response.json();
                this.historyFiles = files;
            } catch (error) {
                console.error("Failed to fetch history file list:", error);
            }
        },
        // Region: Data Sheet; Add data points through button
        addData() {
            if (this.newTimestamp && this.newValue !== null) {
                this.dataList.push({
                    timestamp: this.newTimestamp,
                    value: this.newValue
                });
                this.newTimestamp = '';
                this.newValue = null;
                this.updateChartFromEdit(); // Call main function
            }
        },
        updateTimestamp(index, event) {
            this.dataList[index].timestamp = event.target.innerText;
            this.updateChartFromEdit();
        },
        updateValue(index, event) {
            const val = parseFloat(event.target.innerText);
            if (!isNaN(val)) {
                this.dataList[index].value = val;
                this.updateChartFromEdit();
            }
        },
        // Region: Upper button section; load exist csv file from uploads folder
        async loadSelectedFile() {
            if (!this.selectedFile) return;
            try {
                const response = await fetch(`/load_history_data/${encodeURIComponent(this.selectedFile)}`);
                const data = await response.json();
                this.dataList =data;
                drawChartFrom(this.dataList);
                console.log("loaded", data)
            } catch (error) {
                console.error("Failed to load history file list:", error);
            }
        },
        // Image fetch from camera module
        async fetchImageList() {
            const res =  await fetch('/image_list');
            this.imageList = await res.json();
            if (this.currentImageIndex === null && this.imageList.length > 0) {
                this.currentImageIndex = 0;
            }
        },
        selectImage(index) {
            this.currentImageIndex = index;
        },
    },
    mounted() {
        this.updateChartFromEdit();
        this.loadHistoryFiles();
        this.fetchImageList();
        window.addEventListener('keydown', this.handleArrowKey);
        setInterval(this.fetchImageList, 5000);
    },
});

const vm = app.mount('#app');
window.app = vm;

// Delete graph and data points
async function deleteAndReload() {
    try {
        const response = await fetch('/delete_data', { method: 'POST' });
        const data = await response.json();
        if (data.status === "success") {
            // Initialize
            app.dataList =[]; // Clean Vue
            drawChartFrom([]);
            alert("Graph has been reset!");
        } else {
            alert("Deletion Fail：" + (data.message || "LOL"));
        }
    } catch (error) {
        alert("Fail：" + error.message);
    }
}

// Load save or history csv file
async function loadHistoryList() {
    const response = await fetch('/list_history');
    const files = await response.json();
    const listDiv = document.getElementById('historyList');
    listDiv.innerHTML = files.map(file => `
           <div>
                <a href="/download_history/${file}" download>${file}</a>
            </div>
        `).join('');
}

// Download Option for csv
function downloadCSV() {
    window.location.href = "http://10.0.0.194:5000/download_csv";
}
