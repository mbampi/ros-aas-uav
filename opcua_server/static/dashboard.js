class UAVDashboard {
    constructor() {
        this.properties = new Map();
        this.charts = new Map();
        this.eventLog = [];
        this.logPaused = false;
        this.maxLogEntries = 100;
        this.totalEvents = 0;
        this.serverStartTs = null; // seconds since epoch from server
        this.summaryLastUpdate = null;
        this.pollingActive = false;
        this.pollInterval = null;
        
        this.initializeUI();
        this.setupEventListeners();
        this.initializeCharts();
        this.startPolling();
        this.startUptimeTimer();
    }

    initializeUI() {
        // Initialize summary cards
        this.elements = {
            totalEvents: document.getElementById('totalEvents'),
            activeProperties: document.getElementById('activeProperties'),
            uptime: document.getElementById('uptime'),
            propertiesGrid: document.getElementById('propertiesGrid'),
            logContainer: document.getElementById('logContainer'),
            connectionStatus: document.getElementById('connectionStatus'),
            statusText: document.getElementById('statusText'),
            lastUpdate: document.getElementById('lastUpdate')
        };
    }

    setupEventListeners() {
        // Log controls
        document.getElementById('clearLogBtn').addEventListener('click', () => {
            this.clearLog();
        });

        document.getElementById('pauseLogBtn').addEventListener('click', (e) => {
            this.toggleLogPause(e.target);
        });

        document.getElementById('maxLogEntries').addEventListener('change', (e) => {
            this.maxLogEntries = parseInt(e.target.value);
            this.trimLog();
        });

        // Refresh rate control
        const refreshSelect = document.getElementById('refreshRate');
        if (refreshSelect) {
            this.pollIntervalMs = parseInt(localStorage.getItem('ui_poll_ms') || '500');
            refreshSelect.value = String(this.pollIntervalMs);
            refreshSelect.addEventListener('change', (e) => {
                const ms = parseInt(e.target.value);
                if (!isNaN(ms) && ms > 0) {
                    this.pollIntervalMs = ms;
                    localStorage.setItem('ui_poll_ms', String(ms));
                    // Restart polling with new interval
                    if (this.pollingActive) {
                        this.stopPolling();
                        this.startPolling();
                    }
                }
            });
        } else {
            this.pollIntervalMs = 500; // Default 0.5 seconds
        }
    }

    initializeCharts() {
        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'Data Points'
                    }
                },
                y: {
                    beginAtZero: false,
                    title: {
                        display: true,
                        text: 'Value'
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            elements: {
                point: {
                    radius: 3
                },
                line: {
                    tension: 0.1
                }
            }
        };

        // Battery Chart
        const batteryCtx = document.getElementById('batteryChart').getContext('2d');
        this.charts.set('battery', new Chart(batteryCtx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Battery Level (%)',
                    data: [],
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    fill: true
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'Battery Level'
                    }
                }
            }
        }));

        // Altitude Chart
        const altitudeCtx = document.getElementById('altitudeChart').getContext('2d');
        this.charts.set('altitude', new Chart(altitudeCtx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Altitude (m)',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    fill: true
                }]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'Altitude'
                    }
                }
            }
        }));

        // Speed Chart
        const speedCtx = document.getElementById('speedChart').getContext('2d');
        this.charts.set('speed', new Chart(speedCtx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Horizontal Speed (m/s)',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        fill: false
                    },
                    {
                        label: 'Vertical Speed (m/s)',
                        data: [],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        fill: false
                    }
                ]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'Speed'
                    }
                }
            }
        }));

        // Attitude Chart
        const attitudeCtx = document.getElementById('attitudeChart').getContext('2d');
        this.charts.set('attitude', new Chart(attitudeCtx, {
            type: 'line',
            data: {
                datasets: [
                    {
                        label: 'Pitch (°)',
                        data: [],
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        fill: false
                    },
                    {
                        label: 'Heading (°)',
                        data: [],
                        borderColor: '#06b6d4',
                        backgroundColor: 'rgba(6, 182, 212, 0.1)',
                        fill: false
                    }
                ]
            },
            options: {
                ...chartOptions,
                plugins: {
                    ...chartOptions.plugins,
                    title: {
                        display: true,
                        text: 'Attitude'
                    }
                }
            }
        }));
    }


    updateConnectionStatus(connected) {
        const dot = this.elements.connectionStatus.querySelector('.status-dot');
        const text = this.elements.statusText;

        if (connected) {
            dot.className = 'status-dot connected';
            text.textContent = 'Connected';
        } else {
            dot.className = 'status-dot disconnected';
            text.textContent = 'Disconnected';
        }
    }

    handleVariableUpdate(data) {
        const { variable, value, server_recv_ts, node_id } = data;

        if (!variable) return;

        // Update property data
        if (!this.properties.has(variable)) {
            this.properties.set(variable, {
                name: variable,
                value: null,
                lastValue: null,
                eventCount: 0,
                lastUpdate: null,
                nodeId: node_id,
                history: []
            });
            this.createPropertyCard(variable);
        }

        const property = this.properties.get(variable);
        property.lastValue = property.value;
        property.value = value;
        property.eventCount++;
        property.lastUpdate = new Date(server_recv_ts * 1000);

        // Keep history for charts (last 50 points)
        property.history.push({
            x: property.lastUpdate,
            y: this.parseNumericValue(value)
        });
        if (property.history.length > 50) {
            property.history.shift();
        }

        // Update UI
        this.updatePropertyCard(variable);
        this.updateCharts(variable, property);
        this.addLogEntry(data);

        // Update totals
        this.totalEvents++;
        this.updateSummaryCards();
        this.elements.lastUpdate.textContent = `Last Update: ${new Date().toLocaleTimeString()}`;
    }

    parseNumericValue(value) {
        if (typeof value === 'number') return value;
        if (typeof value === 'string') {
            const num = parseFloat(value);
            return isNaN(num) ? 0 : num;
        }
        return 0;
    }

    createPropertyCard(variableName) {
        const property = this.properties.get(variableName);
        const card = document.createElement('div');
        card.className = 'property-card fade-in';
        card.id = `property-${variableName}`;

        card.innerHTML = `
            <div class="property-header">
                <div class="property-name">${variableName}</div>
                <div class="property-status active">Active</div>
            </div>
            <div class="property-details">
                <div class="property-detail">
                    <div class="property-detail-label">Current Value</div>
                    <div class="property-detail-value property-value">--</div>
                </div>
                <div class="property-detail">
                    <div class="property-detail-label">Events</div>
                    <div class="property-detail-value property-events">0</div>
                </div>
                <div class="property-detail">
                    <div class="property-detail-label">Last Update</div>
                    <div class="property-detail-value property-timestamp">Never</div>
                </div>
                <div class="property-detail">
                    <div class="property-detail-label">Node ID</div>
                    <div class="property-detail-value" style="font-size: 0.75rem;">${property.nodeId || 'Unknown'}</div>
                </div>
            </div>
        `;

        this.elements.propertiesGrid.appendChild(card);
    }

    updatePropertyCard(variableName, hasValueChanged = false) {
        const property = this.properties.get(variableName);
        const card = document.getElementById(`property-${variableName}`);

        if (!card) return;

        const valueElement = card.querySelector('.property-value');
        const eventsElement = card.querySelector('.property-events');
        const timestampElement = card.querySelector('.property-timestamp');

        // Format value based on type
        let displayValue = property.value;
        if (typeof displayValue === 'number') {
            displayValue = displayValue.toFixed(2);
        } else if (typeof displayValue === 'object') {
            displayValue = JSON.stringify(displayValue);
        } else if (displayValue === null || displayValue === undefined) {
            displayValue = '--';
        }

        // Only update DOM if values have changed to prevent unnecessary updates
        if (valueElement.textContent !== displayValue) {
            valueElement.textContent = displayValue;
        }
        if (eventsElement.textContent !== String(property.eventCount)) {
            eventsElement.textContent = property.eventCount;
        }
        const timeText = property.lastUpdate ? property.lastUpdate.toLocaleTimeString() : 'Never';
        if (timestampElement.textContent !== timeText) {
            timestampElement.textContent = timeText;
        }

        // Only add highlight animation when value actually changed (not just on every poll)
        if (hasValueChanged) {
            card.classList.add('highlight');
            setTimeout(() => card.classList.remove('highlight'), 800);
        }
    }

    updateCharts(variableName, property) {
        const numericValue = this.parseNumericValue(property.value);

        // Update relevant charts based on variable name
        const varLower = variableName.toLowerCase();

        if (varLower.includes('battery') || varLower.includes('currentbatterylevel')) {
            this.updateChart('battery', 0, numericValue);
        } else if (varLower.includes('altitude')) {
            this.updateChart('altitude', 0, numericValue);
        } else if (varLower.includes('horizontalspeed')) {
            this.updateChart('speed', 0, numericValue);
        } else if (varLower.includes('verticalspeed')) {
            this.updateChart('speed', 1, numericValue);
        } else if (varLower.includes('pitch')) {
            this.updateChart('attitude', 0, numericValue);
        } else if (varLower.includes('heading')) {
            this.updateChart('attitude', 1, numericValue);
        }
    }

    updateChart(chartName, datasetIndex, value) {
        const chart = this.charts.get(chartName);
        if (!chart || !chart.data.datasets[datasetIndex]) return;

        const dataset = chart.data.datasets[datasetIndex];

        // Add new data point with simple x index
        const nextX = dataset.data.length;
        dataset.data.push({ x: nextX, y: value });

        // Keep only last 30 points
        if (dataset.data.length > 30) {
            dataset.data.shift();
            // Recalculate x values to keep them sequential
            dataset.data.forEach((point, index) => {
                point.x = index;
            });
        }

        chart.update('none');
    }

    addLogEntry(data) {
        if (this.logPaused) return;

        const entry = {
            timestamp: new Date(data.server_recv_ts * 1000),
            variable: data.variable,
            value: data.value,
            event: data.event || 'variable_updated'
        };

        this.eventLog.unshift(entry);
        this.trimLog();
        this.renderLog();
    }

    renderLog() {
        const container = this.elements.logContainer;
        container.innerHTML = '';

        this.eventLog.forEach(entry => {
            const div = document.createElement('div');
            div.className = 'log-entry';

            let valueDisplay = entry.value;
            if (typeof valueDisplay === 'object') {
                valueDisplay = JSON.stringify(valueDisplay);
            }

            div.innerHTML = `
                <span class="log-timestamp">${entry.timestamp.toLocaleTimeString()}</span>
                <span class="log-event">[${entry.event}]</span>
                <span class="log-variable">${entry.variable}</span>
                <span class="log-text">=</span>
                <span class="log-value">${valueDisplay}</span>
            `;

            container.appendChild(div);
        });
    }

    trimLog() {
        if (this.eventLog.length > this.maxLogEntries) {
            this.eventLog = this.eventLog.slice(0, this.maxLogEntries);
        }
    }

    clearLog() {
        this.eventLog = [];
        this.elements.logContainer.innerHTML = '';
    }

    toggleLogPause(button) {
        this.logPaused = !this.logPaused;
        button.textContent = this.logPaused ? 'Resume' : 'Pause';
        button.classList.toggle('paused', this.logPaused);
    }

    updateSummaryCards() {
        this.elements.totalEvents.textContent = this.totalEvents.toLocaleString();
        this.elements.activeProperties.textContent = this.properties.size;
    }

    startUptimeTimer() {
        setInterval(() => {
            if (this.serverStartTs) {
                const uptimeMs = Date.now() - this.serverStartTs * 1000;
                const hours = Math.floor(uptimeMs / (1000 * 60 * 60));
                const minutes = Math.floor((uptimeMs % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((uptimeMs % (1000 * 60)) / 1000);
                this.elements.uptime.textContent = `${hours.toString().padStart(2, '0')}:${minutes
                    .toString()
                    .padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            } else {
                this.elements.uptime.textContent = '— — : — — : — —';
            }
        }, 1000);
    }

    updateServerStats(stats) {
        // Persist server start time and last update for accurate uptime across refreshes
        if (stats && stats.start_time) {
            this.serverStartTs = stats.start_time; // seconds epoch
        }
        if (stats && stats.last_update) {
            this.summaryLastUpdate = stats.last_update;
            this.elements.lastUpdate.textContent = `Last Update: ${new Date(this.summaryLastUpdate * 1000).toLocaleTimeString()}`;
        }
        // Update totals if present
        if (stats && typeof stats.total_events === 'number') {
            this.totalEvents = stats.total_events;
            this.updateSummaryCards();
        }
        console.log('Server stats:', stats);
    }

    startPolling() {
        if (this.pollingActive) {
            return;
        }
        console.log('Starting API polling...');
        this.pollingActive = true;
        
        // Start polling immediately
        this.pollData();
        
        this.pollInterval = setInterval(() => {
            this.pollData();
        }, this.pollIntervalMs || 500); // Default 0.5 seconds
    }

    stopPolling() {
        if (this.pollingActive && this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
            this.pollingActive = false;
            console.log('Stopped polling.');
        }
    }

    pollData() {
        fetch('/api/stats')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('API data received:', data);
                
                // Show connected status when we successfully fetch data
                this.updateConnectionStatus(true);

                // Update summary stats
                if (data.summary) {
                    this.totalEvents = data.summary.total_events || 0;
                    this.updateSummaryCards();
                    if (data.summary.last_update) {
                        this.summaryLastUpdate = data.summary.last_update;
                        this.elements.lastUpdate.textContent = `Last Update: ${new Date(this.summaryLastUpdate * 1000).toLocaleTimeString()}`;
                    }
                    if (data.summary.start_time) {
                        this.serverStartTs = data.summary.start_time;
                    }
                }

                // Update properties
                if (data.properties) {
                    Object.entries(data.properties).forEach(([name, propData]) => {
                        this.updatePropertyFromAPI(name, propData);
                    });
                }
            })
            .catch(error => {
                console.error('API polling failed:', error);
                // Show disconnected status when polling fails
                this.updateConnectionStatus(false);
            });
    }

    updatePropertyFromAPI(name, propData) {
        // Create property if it doesn't exist
        if (!this.properties.has(name)) {
            this.properties.set(name, {
                name: name,
                value: null,
                lastValue: null,
                eventCount: 0,
                lastUpdate: null,
                nodeId: propData.node_id,
                history: []
            });
            this.createPropertyCard(name);
        }

        const property = this.properties.get(name);
        const hasValueChanged = property.value !== propData.value;

        // Update property data
        property.lastValue = property.value;
        property.value = propData.value;
        property.eventCount = propData.event_count || 0;
        property.lastUpdate = propData.last_update ? new Date(propData.last_update * 1000) : null;

        // Update UI elements with change information
        this.updatePropertyCard(name, hasValueChanged);

        // Update charts if value changed
        if (hasValueChanged && propData.value !== null && propData.value !== undefined) {
            this.updateCharts(name, property);
            
            // Add to event log only when value actually changes
            if (!this.logPaused) {
                this.addLogEntry({
                    variable: name,
                    value: propData.value,
                    server_recv_ts: propData.last_update || (Date.now() / 1000),
                    event: 'value_changed'
                });
            }
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UAVDashboard();
});
