// Main script for doctor dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log("Doctor dashboard script loaded");

    // Initialize charts
    initCharts();
    
    // Setup appointment tabs
    setupAppointmentTabs();
    
    // Initialize calendar
    initCalendar();
    
    // Setup queue functionality
    setupQueueToggle();
    
    // Handle initial page state
    handleInitialPageState();
});

// Handle initial page state
function handleInitialPageState() {
    // Update wait times once on page load
    updateWaitTimes();
    
    // Initialize queue buttons' event listeners
    initializeQueueButtons();
    
    // Setup auto-fadeout for messages
    setupMessagesFadeout();
}

// Setup messages fadeout
function setupMessagesFadeout() {
    // Messages will auto-fadeout due to CSS animation
    // Just make sure close buttons work
    document.querySelectorAll('.close-message').forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.remove();
        });
    });
    
    // Create test message functions for development if needed
    window.showSuccessMessage = function(message) {
        showNotification(message, 'success');
    };
    
    window.showErrorMessage = function(message) {
        showNotification(message, 'error');
    };
}

// Initialize all charts using ECharts
function initCharts() {
    // Check if ECharts is loaded
    if (typeof echarts === 'undefined') {
        console.error('ECharts library not loaded');
        return;
    }
    
    // Get chart data from hidden element
    let appointmentsData = [];
    let daysData = [];
    let earningsData = [];
    let monthlyData = [];
    let monthNames = [];
    let ratingData = [];
    
    try {
        const chartData = document.getElementById('chart-data');
        if (chartData) {
            appointmentsData = JSON.parse(chartData.getAttribute('data-appointments') || '[]');
            daysData = JSON.parse(chartData.getAttribute('data-days') || '[]');
            earningsData = JSON.parse(chartData.getAttribute('data-earnings') || '[]');
            monthlyData = JSON.parse(chartData.getAttribute('data-monthly') || '[]');
            monthNames = JSON.parse(chartData.getAttribute('data-months') || '[]');
            ratingData = JSON.parse(chartData.getAttribute('data-ratings') || '[]');
            
            console.log("Chart data loaded:", {
                appointments: appointmentsData,
                days: daysData,
                earnings: earningsData
            });
        } else {
            console.warn("Chart data element not found");
        }
    } catch (error) {
        console.error('Error parsing chart data:', error);
    }
    
    // Appointments Chart - matches HTML ID
    const appointmentsChartElement = document.getElementById('appointments-chart');
    if (appointmentsChartElement) {
        const appointmentsChart = echarts.init(appointmentsChartElement);
        const appointmentsOption = {
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '10%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: daysData.length > 0 ? daysData : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                axisLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#999',
                    fontSize: 10
                }
            },
            yAxis: {
                type: 'value',
                show: false
            },
            series: [{
                data: appointmentsData.length > 0 ? appointmentsData : [4, 6, 5, 8, 10, 6, 7],
                type: 'line',
                smooth: true,
                symbol: 'circle',
                symbolSize: 6,
                lineStyle: {
                    color: '#5470c6',
                    width: 3
                },
                itemStyle: {
                    color: '#5470c6'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: 'rgba(84, 112, 198, 0.3)'
                        }, {
                            offset: 1,
                            color: 'rgba(84, 112, 198, 0.1)'
                        }]
                    }
                }
            }]
        };
        appointmentsChart.setOption(appointmentsOption);
        console.log("Appointments chart initialized");
    } else {
        console.warn("Appointments chart element not found");
    }
    
    // Revenue Chart - matches HTML ID
    const revenueChartElement = document.getElementById('revenue-chart');
    if (revenueChartElement) {
        const revenueChart = echarts.init(revenueChartElement);
        const revenueOption = {
            grid: {
                left: '3%',
                right: '4%',
                bottom: '3%',
                top: '10%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: daysData.length > 0 ? daysData : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                axisLine: {
                    show: false
                },
                axisTick: {
                    show: false
                },
                axisLabel: {
                    color: '#999',
                    fontSize: 10
                }
            },
            yAxis: {
                type: 'value',
                show: false
            },
            series: [{
                data: earningsData.length > 0 ? earningsData : [300, 450, 380, 650, 800, 560, 700],
                type: 'bar',
                barWidth: '60%',
                itemStyle: {
                    color: '#67c23a',
                    borderRadius: [3, 3, 0, 0]
                }
            }]
        };
        revenueChart.setOption(revenueOption);
        console.log("Revenue chart initialized");
    } else {
        console.warn("Revenue chart element not found");
    }
    
    // Handle window resize
    window.addEventListener('resize', function() {
        if (appointmentsChartElement) {
            echarts.getInstanceByDom(appointmentsChartElement)?.resize();
        }
        if (revenueChartElement) {
            echarts.getInstanceByDom(revenueChartElement)?.resize();
        }
    });
}

// Setup appointment tab functionality
function setupAppointmentTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const appointmentCards = document.querySelectorAll('.appointment-card');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('active-tab');
                btn.classList.add('inactive-tab');
            });
            
            // Add active class to clicked button
            this.classList.add('active-tab');
            this.classList.remove('inactive-tab');
            
            // Get the selected tab type
            const tabType = this.id.split('-')[1];
            
            // Show/hide appropriate appointment cards
            appointmentCards.forEach(card => {
                if (tabType === 'all') {
                    card.style.display = 'block';
                } else {
                    const cardType = card.getAttribute('data-type');
                    card.style.display = (tabType === cardType) ? 'block' : 'none';
                }
            });
        });
    });
}

// Initialize calendar with events
function initCalendar() {
    const calendarElement = document.getElementById('days-grid');
    const currentMonthElement = document.getElementById('current-month');
    const prevMonthButton = document.getElementById('prev-month');
    const nextMonthButton = document.getElementById('next-month');
    
    // Get current date
    const today = new Date();
    let currentMonth = today.getMonth();
    let currentYear = today.getFullYear();
    
    // Get events data from server
    let calendarEvents = [];
    try {
        const eventsData = document.getElementById('calendar-events');
        if (eventsData && eventsData.getAttribute('data-events')) {
            calendarEvents = JSON.parse(eventsData.getAttribute('data-events'));
            console.log('Calendar events loaded:', calendarEvents);
        } else {
            console.warn('No calendar events data found');
        }
    } catch (error) {
        console.error('Error parsing calendar events:', error);
    }
    
    // Render initial calendar
    renderCalendar(currentMonth, currentYear);
    
    // Add event listeners for month navigation
    prevMonthButton.addEventListener('click', function() {
        currentMonth--;
        if (currentMonth < 0) {
            currentMonth = 11;
            currentYear--;
        }
        renderCalendar(currentMonth, currentYear);
    });
    
    nextMonthButton.addEventListener('click', function() {
        currentMonth++;
        if (currentMonth > 11) {
            currentMonth = 0;
            currentYear++;
        }
        renderCalendar(currentMonth, currentYear);
    });
    
    // Function to render calendar for given month and year
    function renderCalendar(month, year) {
        // Update month display
        const monthNames = ['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December'];
        currentMonthElement.textContent = `${monthNames[month]} ${year}`;
        
        // Clear previous calendar
        calendarElement.innerHTML = '';
        
        // Get first day of month and number of days
        const firstDay = new Date(year, month, 1).getDay();
        const daysInMonth = new Date(year, month + 1, 0).getDate();
        
        // Add empty cells for days before first of month
        for (let i = 0; i < firstDay; i++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'day empty';
            calendarElement.appendChild(dayElement);
        }
        
        // Add days of month
        for (let day = 1; day <= daysInMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.className = 'day';
            
            // Check if this is today
            const currentDate = new Date();
            if (day === currentDate.getDate() && month === currentDate.getMonth() && year === currentDate.getFullYear()) {
                dayElement.classList.add('today');
            }
            
            // Add date number
            const dateNumber = document.createElement('span');
            dateNumber.className = 'date-number';
            dateNumber.textContent = day;
            dayElement.appendChild(dateNumber);
            
            // Add event indicators if there are events on this day
            const formattedDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const dayEvents = calendarEvents.filter(event => event.date === formattedDate);
            
            if (dayEvents.length > 0) {
                dayElement.classList.add('has-events');
                
                if (dayEvents.length <= 3) {
                    // Show dot indicators for up to 3 events
                    const indicatorsContainer = document.createElement('div');
                    indicatorsContainer.className = 'event-indicators';
                    
                    dayEvents.forEach(event => {
                        const indicator = document.createElement('span');
                        indicator.className = `event-dot ${event.status || 'default'}`;
                        indicatorsContainer.appendChild(indicator);
                    });
                    
                    dayElement.appendChild(indicatorsContainer);
                } else {
                    // Show count for more than 3 events
                    const countIndicator = document.createElement('div');
                    countIndicator.className = 'event-count';
                    countIndicator.textContent = dayEvents.length;
                    dayElement.appendChild(countIndicator);
                }
                
                // Add click handler to show events
                dayElement.addEventListener('click', function() {
                    // Display event information
                    const dateDisplay = `${monthNames[month]} ${day}, ${year}`;
                    console.log(`Clicked on ${dateDisplay}, events:`, dayEvents);
                    
                    // Show an alert with event info for demo purposes
                    const eventSummary = dayEvents.map(event => 
                        `${event.time}: ${event.title} (${event.status})`
                    ).join('\n');
                    
                    alert(`Appointments on ${dateDisplay}:\n\n${eventSummary}`);
                });
            }
            
            calendarElement.appendChild(dayElement);
        }
    }
}

// Setup queue toggle
function setupQueueToggle() {
    const autoRefreshToggle = document.getElementById('auto-refresh-toggle');
    const queueList = document.querySelector('.queue-list');
    let refreshInterval;
    
    if (autoRefreshToggle && queueList) {
        // Setup initial auto-refresh if toggle is checked
        if (autoRefreshToggle.checked) {
            startAutoRefresh();
        }
        
        // Listen for toggle changes
        autoRefreshToggle.addEventListener('change', function() {
            if (this.checked) {
                startAutoRefresh();
                showNotification('Auto-refresh enabled', 'success');
            } else {
                stopAutoRefresh();
                showNotification('Auto-refresh disabled', 'info');
            }
        });
    }
    
    // Initialize message and view detail buttons
    initializeQueueButtons();
    
    // Function to handle auto-refresh
    function startAutoRefresh() {
        // Clear any existing interval
        if (refreshInterval) {
            clearInterval(refreshInterval);
        }
        
        // Set new interval to refresh the queue every 30 seconds
        refreshInterval = setInterval(refreshQueueData, 30000); // 30 seconds
        console.log('Auto-refresh started');
    }
    
    // Function to stop auto-refresh
    function stopAutoRefresh() {
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
            console.log('Auto-refresh stopped');
        }
    }
    
    // Function to refresh queue data via AJAX
    function refreshQueueData() {
        console.log('Refreshing queue data...');
        
        // Simulated Ajax call to refresh queue
        // In a real implementation, this would be a fetch or XMLHttpRequest to the server
        
        // Simple animation to show refresh is happening
        const queueItems = document.querySelectorAll('.queue-item');
        queueItems.forEach(item => {
            item.style.opacity = '0.6';
        });
        
        // Simulate network delay and response
        setTimeout(() => {
            // Ajax would update data here
            queueItems.forEach(item => {
                item.style.opacity = '1';
            });
            
            // Update the wait times
            updateWaitTimes();
            
            console.log('Queue refreshed');
        }, 1000);
    }
}

// Update wait times without full refresh
function updateWaitTimes() {
    const waitTimeElements = document.querySelectorAll('.wait-time');
    waitTimeElements.forEach(element => {
        const text = element.textContent;
        
        // Parse the current time
        if (text.includes('Waiting')) {
            // If already waiting, increase the wait time
            const minutes = parseInt(text.match(/\d+/)[0]);
            element.textContent = `Waiting ${minutes + 1} min`;
        } else if (text.includes('In')) {
            // If appointment coming up, decrease the time
            const minutes = parseInt(text.match(/\d+/)[0]);
            if (minutes > 1) {
                element.textContent = `In ${minutes - 1} min`;
            } else {
                // If just 1 minute left, mark as arriving
                element.textContent = 'Arriving now';
                element.style.color = '#10b981';
                element.style.fontWeight = 'bold';
            }
        }
    });
}

// Initialize queue buttons functionality
function initializeQueueButtons() {
    // View patient buttons already handled in main script
}

// Patient info modal
function openPatientInfoModal(patientId) {
    // Show loading state
    document.getElementById('patient-info-modal').style.display = 'flex';
    document.getElementById('patient-info-body').innerHTML = 
        `<p>Loading patient information...</p>`;
    
    try {
        // Get the appointments data from the hidden div
        const appointmentsDataElement = document.getElementById('appointments-data');
        if (!appointmentsDataElement) {
            throw new Error('Appointments data element not found');
        }
        
        const appointmentsData = JSON.parse(appointmentsDataElement.getAttribute('data-appointments') || '[]');
        console.log('Loaded appointments data:', appointmentsData);
        
        // Find the appointment with the matching ID
        const booking = appointmentsData.find(booking => booking.id == patientId);
        
        if (!booking) {
            throw new Error(`Booking with ID ${patientId} not found`);
        }
        
        console.log('Found booking data:', booking);
        
        // Render the booking details
        renderPatientDetails(booking);
    } catch (error) {
        console.error('Error loading booking details:', error);
        document.getElementById('patient-info-body').innerHTML = 
            `<div class="error-message">
                <p><i class="ri-error-warning-line"></i> Error loading patient details</p>
                <p>${error.message}</p>
            </div>`;
    }
}

// Render patient details in the modal
function renderPatientDetails(booking) {
    // Format date and time for display
    const appointmentTime = booking.time || '00:00';
    
    // Patient modal content
    document.getElementById('patient-info-body').innerHTML = `
        <div class="patient-profile-header">
            <div class="patient-avatar"><i class="ri-user-3-fill"></i></div>
            <div class="patient-basic-info">
                <h3>${booking.patient_name || 'Unknown Patient'}</h3>
                <p>Booking #${booking.id}</p>
            </div>
        </div>
        <div class="patient-details">
            <div class="detail-group">
                <h4>Appointment Details</h4>
                <p><i class="ri-calendar-event-line"></i> <strong>Scheduled Time:</strong> ${appointmentTime}</p>
                <p><i class="ri-service-line"></i> <strong>Service:</strong> ${booking.type || 'General Consultation'}</p>
                <p><i class="ri-checkbox-circle-line"></i> <strong>Status:</strong> <span class="status-badge ${booking.status}">${booking.status || 'pending'}</span></p>
            </div>
            
            <div class="detail-group">
                <h4>Actions Available</h4>
                <div class="action-buttons" style="margin-top: 10px;">
                    ${booking.status === 'confirmed' ? 
                        `<form method="post" style="display: inline-block; margin-right: 10px;">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                            <input type="hidden" name="booking_id" value="${booking.id}">
                            <input type="hidden" name="action" value="check_in">
                            <button type="submit" class="action-btn primary">Check In Patient</button>
                        </form>` : 
                        booking.status === 'pending' ?
                        `<form method="post" style="display: inline-block; margin-right: 10px;">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                            <input type="hidden" name="booking_id" value="${booking.id}">
                            <input type="hidden" name="action" value="confirm">
                            <button type="submit" class="action-btn primary">Confirm Appointment</button>
                        </form>` :
                        booking.status === 'in_progress' ?
                        `<form method="post" style="display: inline-block; margin-right: 10px;">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${document.querySelector('[name=csrfmiddlewaretoken]').value}">
                            <input type="hidden" name="booking_id" value="${booking.id}">
                            <input type="hidden" name="action" value="complete">
                            <button type="submit" class="action-btn primary">Complete Appointment</button>
                        </form>` :
                        ''}
                </div>
            </div>
        </div>
        
        <button class="close-modal action-btn secondary" style="margin-top: 15px;">Close</button>
    `;
    
    // Setup close button
    document.querySelector('#patient-info-modal .close-modal').addEventListener('click', function() {
        document.getElementById('patient-info-modal').style.display = 'none';
    });
}

// Show message modal
function showMessageModal(patientId) {
    // Create a simple modal for messaging
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    
    modal.innerHTML = `
        <div class="modal-content" style="width: 400px;">
            <div class="modal-header">
                <h2>Message Patient</h2>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <div style="margin-bottom: 15px;">
                    <label for="message-subject" style="display: block; margin-bottom: 5px;">Subject:</label>
                    <input type="text" id="message-subject" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #d1d5db;" placeholder="Appointment Reminder">
                </div>
                <div style="margin-bottom: 15px;">
                    <label for="message-text" style="display: block; margin-bottom: 5px;">Message:</label>
                    <textarea id="message-text" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #d1d5db; min-height: 120px;" placeholder="Enter your message here..."></textarea>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <button class="action-btn secondary close-modal">Cancel</button>
                    <button class="action-btn primary" id="send-message-btn">Send Message</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Setup event listeners
    modal.querySelector('.close-modal').addEventListener('click', function() {
        document.body.removeChild(modal);
    });
    
    modal.querySelector('#send-message-btn').addEventListener('click', function() {
        const subject = document.getElementById('message-subject').value;
        const message = document.getElementById('message-text').value;
        
        if (!message.trim()) {
            showNotification('Please enter a message', 'error');
            return;
        }
        
        // Simulate sending message
        showNotification('Message sent successfully', 'success');
        document.body.removeChild(modal);
    });
    
    // Close when clicking outside
    modal.addEventListener('click', function(event) {
        if (event.target === modal) {
            document.body.removeChild(modal);
        }
    });
}

// Show notification
function showNotification(message, type = 'info') {
    // Look for existing messages container or create one
    let container = document.getElementById('messages-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'messages-container';
        container.className = 'messages-container';
        document.body.appendChild(container);
    }
    
    // Create the message element
    const notification = document.createElement('div');
    notification.className = `message ${type}`;
    notification.innerHTML = `
        ${message}
        <button class="close-message" onclick="this.parentElement.remove()">&times;</button>
    `;
    
    // Add to container
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode === container) {
            notification.remove();
        }
    }, 5000);
}


// Create a self-executing function to avoid polluting the global namespace
(function() {
    // Azure OpenAI configuration
    const endpoint = "https://neela-maa2tdpw-swedencentral.openai.azure.com/openai/deployments/CureBot/chat/completions?api-version=2025-01-01-preview";
    const apiKey = "256OQtOitExk9M6g7cniyb3vnSgv07R1YzwimDBwQHWbWonsS3BDJQQJ99BEACfhMk5XJ3w3AAAAACOGPHka";
    
    // Create and inject CSS
    const injectStyles = () => {
        const styleElement = document.createElement('style');
        styleElement.textContent = `
            /* Base styles */
            body {
                font-family: 'Roboto', 'Segoe UI', sans-serif;
                margin: 0;
                padding: 0;
                background-color: #f8fafc;
                color: #334155;
            }
            
            /* Toggle Button with enhanced design */
            .chat-toggle {
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 65px;
                height: 65px;
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                color: white;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                cursor: pointer;
                box-shadow: 0 6px 16px rgba(0, 120, 215, 0.3);
                z-index: 1000;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                border: none;
                outline: none;
            }
            
            .chat-toggle:hover {
                transform: translateY(-5px) scale(1.05);
                box-shadow: 0 10px 20px rgba(0, 120, 215, 0.4);
            }
            
            .chat-toggle:active {
                transform: translateY(0) scale(0.95);
            }
            
            .chat-toggle .icon {
                font-size: 28px;
                transition: all 0.3s ease;
            }
            
            .chat-toggle::before {
                content: '';
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.2);
                transform: scale(0);
                transition: transform 0.5s ease;
            }
            
            .chat-toggle:hover::before {
                transform: scale(1.2);
                opacity: 0;
            }
            
            /* Pulse animation for the toggle button */
            .chat-toggle::after {
                content: '';
                position: absolute;
                width: 100%;
                height: 100%;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.4);
                z-index: -1;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% {
                    transform: scale(1);
                    opacity: 0.7;
                }
                70% {
                    transform: scale(1.3);
                    opacity: 0;
                }
                100% {
                    transform: scale(1);
                    opacity: 0;
                }
            }
            
            /* Chat Container */
            .chat-container {
                position: fixed;
                bottom: 100px;
                right: 30px;
                width: 380px;
                height: 520px;
                background-color: white;
                border-radius: 20px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                z-index: 999;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                opacity: 0;
                pointer-events: none;
                transform: translateY(20px) scale(0.95);
                border: 1px solid rgba(0, 120, 215, 0.1);
            }
            
            .chat-container.active {
                opacity: 1;
                pointer-events: all;
                transform: translateY(0) scale(1);
            }
  
            /* Chat Header */
            .chat-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 16px 20px;
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                color: white;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
            
            .chat-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-weight: 600;
                font-size: 18px;
            }
            
            .chat-logo {
                width: 24px;
                height: 24px;
                background-color: white;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #2563eb;
                font-size: 14px;
                font-weight: bold;
            }
            
            .chat-close {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                font-size: 20px;
                padding: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                transition: background 0.3s;
            }
            
            .chat-close:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            /* Messages area */
            .chat-messages {
                flex: 1;
                padding: 20px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 16px;
                scroll-behavior: smooth;
            }
            
            .message {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 18px;
                line-height: 1.4;
                font-size: 15px;
                word-wrap: break-word;
                position: relative;
                animation: fadeIn 0.3s ease-out;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .message.user {
                align-self: flex-end;
                background: #e2f1ff;
                color: #1e40af;
                border-bottom-right-radius: 4px;
            }
            
            .message.bot {
                align-self: flex-start;
                background: #f1f5f9;
                color: #334155;
                border-bottom-left-radius: 4px;
            }
            
            .typing-indicator {
                align-self: flex-start;
                background: #f1f5f9;
                color: #64748b;
                padding: 12px 16px;
                border-radius: 18px;
                border-bottom-left-radius: 4px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .typing-dot {
                width: 8px;
                height: 8px;
                background: #64748b;
                border-radius: 50%;
                animation: typingAnimation 1.4s infinite ease-in-out;
            }
            
            .typing-dot:nth-child(1) { animation-delay: 0s; }
            .typing-dot:nth-child(2) { animation-delay: 0.2s; }
            .typing-dot:nth-child(3) { animation-delay: 0.4s; }
            
            @keyframes typingAnimation {
                0%, 60%, 100% { transform: translateY(0); }
                30% { transform: translateY(-5px); }
            }
            
            /* Input area */
            .chat-input-container {
                padding: 16px;
                background-color: #fff;
                border-top: 1px solid #e5e7eb;
            }
            
            .chat-input-form {
                display: flex;
                gap: 10px;
            }
            
            .chat-input {
                flex: 1;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 24px;
                outline: none;
                font-size: 15px;
                transition: border-color 0.3s, box-shadow 0.3s;
                font-family: inherit;
                resize: none;
                height: auto;
                overflow-y: hidden;
            }
            
            .chat-input:focus {
                border-color: #2563eb;
                box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
            }
            
            .chat-send-btn {
                width: 44px;
                height: 44px;
                border-radius: 50%;
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                border: none;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: all 0.3s;
                flex-shrink: 0;
            }
            
            .chat-send-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 120, 215, 0.3);
            }
            
            .chat-send-btn:active {
                transform: translateY(0);
            }
            
            .chat-send-btn:disabled {
                background: #cbd5e1;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            /* Welcome message styling */
            .welcome-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 30px 20px;
                height: 100%;
            }
            
            .welcome-icon {
                font-size: 48px;
                margin-bottom: 16px;
                color: #2563eb;
            }
            
            .welcome-title {
                font-size: 22px;
                font-weight: 600;
                color: #1e293b;
                margin-bottom: 12px;
            }
            
            .welcome-message {
                font-size: 16px;
                color: #64748b;
                margin-bottom: 24px;
                line-height: 1.5;
            }
            
            .start-chat-btn {
                padding: 12px 24px;
                background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%);
                color: white;
                border: none;
                border-radius: 24px;
                font-size: 16px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .start-chat-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(0, 120, 215, 0.2);
            }
        `;
        document.head.appendChild(styleElement);
    };
    
    // Create chat toggle button
    const createChatToggle = () => {
        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'chat-toggle';
        toggleBtn.id = 'chatToggle';
        toggleBtn.setAttribute('aria-label', 'Open chat');
        
        const icon = document.createElement('span');
        icon.className = 'icon';
        icon.innerHTML = '💬';
        
        toggleBtn.appendChild(icon);
        document.body.appendChild(toggleBtn);
        
        return toggleBtn;
    };
    
    // Create chat container with full interface
    const createChatContainer = () => {
        const container = document.createElement('div');
        container.className = 'chat-container';
        container.id = 'chatContainer';
        
        // Chat header
        const header = document.createElement('div');
        header.className = 'chat-header';
        
        const title = document.createElement('div');
        title.className = 'chat-title';
        
        const logo = document.createElement('div');
        logo.className = 'chat-logo';
        logo.textContent = 'C';
        
        const titleText = document.createElement('span');
        titleText.textContent = 'CureBot';
        
        title.appendChild(logo);
        title.appendChild(titleText);
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'chat-close';
        closeBtn.innerHTML = '✕';
        closeBtn.setAttribute('aria-label', 'Close chat');
        
        header.appendChild(title);
        header.appendChild(closeBtn);
        
        // Chat messages area
        const messagesArea = document.createElement('div');
        messagesArea.className = 'chat-messages';
        messagesArea.id = 'chatMessages';
        
        // Welcome message (initial state)
        const welcomeContainer = document.createElement('div');
        welcomeContainer.className = 'welcome-container';
        welcomeContainer.id = 'welcomeContainer';
        
        const welcomeIcon = document.createElement('div');
        welcomeIcon.className = 'welcome-icon';
        welcomeIcon.innerHTML = '👋';
        
        const welcomeTitle = document.createElement('h2');
        welcomeTitle.className = 'welcome-title';
        welcomeTitle.textContent = 'Welcome to CureBot';
        
        const welcomeMessage = document.createElement('p');
        welcomeMessage.className = 'welcome-message';
        welcomeMessage.textContent = 'I can help answer your healthcare questions. How can I assist you today?';
        
        const startChatBtn = document.createElement('button');
        startChatBtn.className = 'start-chat-btn';
        startChatBtn.textContent = 'Start Chatting';
        
        welcomeContainer.appendChild(welcomeIcon);
        welcomeContainer.appendChild(welcomeTitle);
        welcomeContainer.appendChild(welcomeMessage);
        welcomeContainer.appendChild(startChatBtn);
        
        messagesArea.appendChild(welcomeContainer);
        
        // Chat input area
        const inputContainer = document.createElement('div');
        inputContainer.className = 'chat-input-container';
        
        const inputForm = document.createElement('form');
        inputForm.className = 'chat-input-form';
        inputForm.id = 'chatInputForm';
        
        const textInput = document.createElement('textarea');
        textInput.className = 'chat-input';
        textInput.id = 'chatInput';
        textInput.placeholder = 'Type your message...';
        textInput.setAttribute('rows', '1');
        
        const sendBtn = document.createElement('button');
        sendBtn.className = 'chat-send-btn';
        sendBtn.type = 'submit';
        sendBtn.innerHTML = '➤';
        sendBtn.setAttribute('aria-label', 'Send message');
        
        inputForm.appendChild(textInput);
        inputForm.appendChild(sendBtn);
        
        inputContainer.appendChild(inputForm);
        
        // Add all elements to container
        container.appendChild(header);
        container.appendChild(messagesArea);
        container.appendChild(inputContainer);
        
        document.body.appendChild(container);
        
        return container;
    };
    
    // Handle chat message sending
    const handleMessageSend = async (inputElement) => {
        const messageText = inputElement.value.trim();
        if (!messageText) return;
        
        // Clear input
        inputElement.value = '';
        
        // Add user message to chat
        addMessage(messageText, 'user');
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Send message to Azure OpenAI
            const response = await sendMessageToAzureOpenAI(messageText);
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add bot response
            if (response) {
                addMessage(response, 'bot');
            } else {
                addMessage("I'm sorry, I couldn't process your request. Please try again.", 'bot');
            }
        } catch (error) {
            console.error('Error processing message:', error);
            
            // Hide typing indicator
            hideTypingIndicator();
            
            // Add error message
            addMessage("I'm sorry, there was an error processing your request. Please try again later.", 'bot');
        }
        
        // Scroll to bottom
        scrollToBottom();
    };
    
    // Add a message to the chat
    const addMessage = (text, sender) => {
        const messagesContainer = document.getElementById('chatMessages');
        const welcomeContainer = document.getElementById('welcomeContainer');
        
        // Remove welcome message if it exists
        if (welcomeContainer && welcomeContainer.parentNode === messagesContainer) {
            messagesContainer.removeChild(welcomeContainer);
        }
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${sender}`;
        messageElement.textContent = text;
        
        messagesContainer.appendChild(messageElement);
        
        // Scroll to bottom
        scrollToBottom();
    };
    
    // Show typing indicator
    const showTypingIndicator = () => {
        const messagesContainer = document.getElementById('chatMessages');
        
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'typing-indicator';
        typingIndicator.id = 'typingIndicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            typingIndicator.appendChild(dot);
        }
        
        messagesContainer.appendChild(typingIndicator);
        
        // Scroll to bottom
        scrollToBottom();
    };
    
    // Hide typing indicator
    const hideTypingIndicator = () => {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.parentNode.removeChild(typingIndicator);
        }
    };
    
    // Scroll chat to bottom
    const scrollToBottom = () => {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };
    
    // Send message to Azure OpenAI API
    const sendMessageToAzureOpenAI = async (message) => {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'api-key': apiKey
                },
                body: JSON.stringify({
                    messages: [
                        { role: "system", content: "You are a helpful healthcare assistant named CureBot. You can answer anything related to medical stuff. But you will not answer anything except it, say It is beyond my learning model! Provide accurate, helpful information on health topics, but always remind users to consult our healthcare professionals from CureClick for medical advice. Prefer to give small responses unless asked for in detail." },
                        { role: "user", content: message }
                    ],
                    max_tokens: 800
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            return data.choices[0].message.content;
        } catch (error) {
            console.error('Error sending message to Azure OpenAI:', error);
            throw error;
        }
    };
    
    // Auto-grow textarea
    const setupTextareaAutoGrow = (textarea) => {
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            const newHeight = Math.min(textarea.scrollHeight, 120);
            textarea.style.height = `${newHeight}px`;
        });
    };
    
    // Initialize chat functionality
    const initChat = () => {
        // Inject styles
        injectStyles();
        
        // Create UI elements
        const chatToggle = createChatToggle();
        const chatContainer = createChatContainer();
        
        // Get elements
        const closeBtn = chatContainer.querySelector('.chat-close');
        const chatForm = document.getElementById('chatInputForm');
        const chatInput = document.getElementById('chatInput');
        const startChatBtn = document.querySelector('.start-chat-btn');
        
        // Setup textarea auto-grow
        setupTextareaAutoGrow(chatInput);
        
        // Toggle chat open/close
        chatToggle.addEventListener('click', () => {
            chatContainer.classList.add('active');
        });
        
        // Close chat
        closeBtn.addEventListener('click', () => {
            chatContainer.classList.remove('active');
        });
        
        // Start chat button click
        if (startChatBtn) {
            startChatBtn.addEventListener('click', () => {
                const welcomeContainer = document.getElementById('welcomeContainer');
                if (welcomeContainer) {
                    welcomeContainer.style.display = 'none';
                }
                
                // Add initial bot message
                addMessage("Hi there! I'm CureBot. How can I help with your health questions today?", 'bot');
                
                // Focus on input
                chatInput.focus();
            });
        }
        
        // Handle form submission
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleMessageSend(chatInput);
        });
        
        // Handle Enter key (submit on Enter, new line on Shift+Enter)
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleMessageSend(chatInput);
            }
        });
    };
    
    // Initialize everything when the DOM is fully loaded
    document.addEventListener('DOMContentLoaded', initChat);
  })();