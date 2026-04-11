/**
 * Chart.js Utilities
 * Wrapper for creating charts using Chart.js library
 */

// Chart color palette
const CHART_COLORS = {
    primary: '#667eea',
    secondary: '#764ba2',
    success: '#28a745',
    danger: '#dc3545',
    warning: '#ffc107',
    info: '#17a2b8',
    light: '#f8f9fa',
    dark: '#1f4788',
    gray: '#748390'
};

const GRADIENT_PRESETS = {
    primary: ['#667eea', '#764ba2'],
    success: ['#28a745', '#20c997'],
    danger: ['#dc3545', '#ff6b6b'],
    warning: ['#ffc107', '#ff9800'],
    info: ['#17a2b8', '#20c997']
};

/**
 * Create a line chart
 */
function createLineChart(elementId, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

/**
 * Create a bar chart
 */
function createBarChart(elementId, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

/**
 * Create a pie chart
 */
function createPieChart(elementId, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'right'
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'pie',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

/**
 * Create a doughnut chart
 */
function createDoughnutChart(elementId, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true,
                position: 'right'
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

/**
 * Create a radar chart
 */
function createRadarChart(elementId, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                display: true
            }
        },
        scales: {
            r: {
                beginAtZero: true
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'radar',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

/**
 * Create a performance chart with gradient
 */
function createPerformanceChart(elementId, labels, data) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(102, 126, 234, 0.3)');
    gradient.addColorStop(1, 'rgba(118, 75, 162, 0.03)');
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Performance',
                data: data,
                borderColor: CHART_COLORS.primary,
                backgroundColor: gradient,
                fill: true,
                tension: 0.4,
                pointRadius: 6,
                pointBackgroundColor: CHART_COLORS.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: CHART_COLORS.gray
                    },
                    grid: {
                        color: 'rgba(200, 200, 200, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: CHART_COLORS.gray
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

/**
 * Get gradient for dataset
 */
function getGradientColor(ctx, colorPreset = 'primary') {
    const colors = GRADIENT_PRESETS[colorPreset] || GRADIENT_PRESETS.primary;
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    
    gradient.addColorStop(0, colors[0]);
    gradient.addColorStop(1, colors[1]);
    
    return gradient;
}

/**
 * Create comparison chart
 */
function createComparisonChart(elementId, labels, datasets) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    const colors = Object.values(CHART_COLORS);
    
    const formattedDatasets = datasets.map((dataset, index) => ({
        label: dataset.label,
        data: dataset.data,
        backgroundColor: colors[index % colors.length],
        borderRadius: 8
    }));
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: formattedDatasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Update chart data dynamically
 */
function updateChartData(chart, newData) {
    chart.data.datasets[0].data = newData;
    chart.update();
}

/**
 * Update chart labels
 */
function updateChartLabels(chart, newLabels) {
    chart.data.labels = newLabels;
    chart.update();
}

/**
 * Destroy chart
 */
function destroyChart(chart) {
    if (chart) {
        chart.destroy();
    }
}
