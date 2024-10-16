from flask import Flask, render_template_string, request, jsonify
import numpy as np

app = Flask(__name__)

def johnson_rule(two_machines_jobs):
    n_jobs = len(two_machines_jobs)
    job_order = []
    jobs = list(range(n_jobs))
    
    while jobs:
        min_time = float('inf')
        selected_job = None
        selected_machine = None
        
        for job in jobs:
            machine_1_time, machine_2_time = two_machines_jobs[job]
            if machine_1_time < min_time or machine_2_time < min_time:
                min_time = min(machine_1_time, machine_2_time)
                selected_job = job
                selected_machine = 0 if machine_1_time < machine_2_time else 1
        
        if selected_machine == 0:
            job_order.insert(0, selected_job)
        else:
            job_order.append(selected_job)
        
        jobs.remove(selected_job)
    
    return job_order

def calculate_makespan(jobs, processing_times):
    n_jobs = len(jobs)
    n_machines = len(processing_times)
    
    completion_time = np.zeros((n_machines, n_jobs))
    
    completion_time[0][0] = processing_times[0][jobs[0]]
    
    for j in range(1, n_jobs):
        completion_time[0][j] = completion_time[0][j-1] + processing_times[0][jobs[j]]
    
    for i in range(1, n_machines):
        for j in range(n_jobs):
            if j == 0:
                completion_time[i][j] = completion_time[i-1][j] + processing_times[i][jobs[j]]
            else:
                completion_time[i][j] = max(completion_time[i-1][j], completion_time[i][j-1]) + processing_times[i][jobs[j]]
    
    return completion_time

def generate_subproblems(processing_times):
    n_jobs, n_machines = processing_times.shape
    subproblems = []
    
    for k in range(1, n_machines):
        subproblem = []
        for job in range(n_jobs):
            machine_1_time = sum(processing_times[job][:k])
            machine_2_time = sum(processing_times[job][k:])
            subproblem.append((machine_1_time, machine_2_time))
        
        subproblems.append(subproblem)
    
    return subproblems

def cds_algorithm(processing_times):
    n_jobs, n_machines = processing_times.shape
    subproblems = generate_subproblems(processing_times)
    
    best_order = None
    best_makespan = float('inf')
    all_orders = []
    
    for i, subproblem in enumerate(subproblems):
        job_order = johnson_rule(subproblem)
        completion_time = calculate_makespan(job_order, processing_times)
        makespan = completion_time[-1][-1]
        
        all_orders.append({
            'iteration': i + 1,
            'order': [j + 1 for j in job_order],
            'makespan': makespan
        })
        
        if makespan < best_makespan:
            best_makespan = makespan
            best_order = job_order
    
    return best_order, best_makespan, all_orders, calculate_makespan(best_order, processing_times)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.json
        processing_times = np.array(data['matrix'])
        best_order, best_makespan, all_orders, completion_time = cds_algorithm(processing_times)
        
        gantt_data = prepare_gantt_data(completion_time, best_order, processing_times)
        
        return jsonify({
            'best_order': [j + 1 for j in best_order],
            'best_makespan': best_makespan,
            'all_orders': all_orders,
            'gantt_data': gantt_data,
            'processing_times': processing_times.tolist()  # Add this line
        })
    return render_template_string(HTML_TEMPLATE)

def prepare_gantt_data(completion_time, job_order, processing_times):
    n_machines, n_jobs = completion_time.shape
    gantt_data = []
    
    for i in range(n_machines):
        for j, job in enumerate(job_order):
            start = completion_time[i][j] - processing_times[i][job] if j > 0 else 0
            duration = processing_times[i][job]
            gantt_data.append({
                'machine': f'Machine {i+1}',
                'job': f'Job {job+1}',
                'start': float(start),
                'end': float(start + duration),
                'duration': float(duration)
            })
    
    return gantt_data

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDS Algorithm Calculator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-4xl font-bold text-center mb-8 text-indigo-600">
            <i class="fas fa-industry mr-2"></i>CDS Algorithm Calculator
        </h1>
        <div class="bg-white rounded-lg shadow-md p-6">
            <div class="mb-6">
                <h2 class="text-2xl font-semibold mb-2">What is the CDS Algorithm?</h2>
                <p class="text-gray-700">The Campbell, Dudek, and Smith (CDS) algorithm is a heuristic method for solving flow shop scheduling problems. It generates a series of two-machine subproblems and applies Johnson's rule to each, selecting the best overall solution.</p>
            </div>
            <div class="flex flex-wrap -mx-2 mb-4">
                <div class="w-full md:w-1/2 px-2 mb-4 md:mb-0">
                    <label for="machines" class="block text-sm font-medium text-gray-700 mb-1">Number of machines:</label>
                    <input type="number" id="machines" min="2" value="3" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="w-full md:w-1/2 px-2">
                    <label for="jobs" class="block text-sm font-medium text-gray-700 mb-1">Number of jobs:</label>
                    <input type="number" id="jobs" min="2" value="4" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
            </div>
            <button id="generate-matrix" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-300 mb-4">
                <i class="fas fa-table mr-2"></i>Generate Matrix
            </button>
            <div id="matrix-container" class="mb-4 overflow-x-auto"></div>
            <button id="calculate" class="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-300">
                <i class="fas fa-calculator mr-2"></i>Apply CDS Algorithm
            </button>
            <div id="results" class="mt-6"></div>
            <div id="explanation" class="mt-6"></div>
            <div id="gantt-chart-container" class="mt-6">
                <canvas id="gantt-chart"></canvas>
            </div>
            <div id="processing-times" class="mt-6"></div>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const generateMatrixBtn = document.getElementById('generate-matrix');
            const calculateBtn = document.getElementById('calculate');
            const matrixContainer = document.getElementById('matrix-container');
            const resultsContainer = document.getElementById('results');
            const explanationContainer = document.getElementById('explanation');
            const ganttChartContainer = document.getElementById('gantt-chart-container');
            const processingTimesContainer = document.getElementById('processing-times');
            let ganttChart = null;

            generateMatrixBtn.addEventListener('click', generateMatrix);
            calculateBtn.addEventListener('click', applyCDSAlgorithm);

            function generateMatrix() {
                const machines = parseInt(document.getElementById('machines').value);
                const jobs = parseInt(document.getElementById('jobs').value);

                let html = '<table class="w-full border-collapse">';
                html += '<tr><th class="border border-gray-300 p-2"></th>';
                for (let j = 0; j < jobs; j++) {
                    html += `<th class="border border-gray-300 p-2">Job ${j + 1}</th>`;
                }
                html += '</tr>';
                for (let i = 0; i < machines; i++) {
                    html += `<tr><th class="border border-gray-300 p-2">Machine ${i + 1}</th>`;
                    for (let j = 0; j < jobs; j++) {
                        html += `<td class="border border-gray-300 p-2">
                            <input type="number" id="cell-${i}-${j}" min="0" value="${Math.floor(Math.random() * 10) + 1}" 
                            class="w-full px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        </td>`;
                    }
                    html += '</tr>';
                }
                html += '</table>';

                matrixContainer.innerHTML = html;
            }

            function applyCDSAlgorithm() {
                const machines = parseInt(document.getElementById('machines').value);
                const jobs = parseInt(document.getElementById('jobs').value);
                let matrix = [];

                for (let i = 0; i < machines; i++) {
                    let row = [];
                    for (let j = 0; j < jobs; j++) {
                        row.push(parseInt(document.getElementById(`cell-${i}-${j}`).value));
                    }
                    matrix.push(row);
                }

                fetch('/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({matrix: matrix}),
                })
                .then(response => response.json())
                .then(data => {
                    displayResults(data);
                    displayExplanation(data);
                    createGanttChart(data.gantt_data);
                    displayProcessingTimes(data.processing_times);
                });
            }

            function displayResults(data) {
                resultsContainer.innerHTML = `
                    <h3 class="text-xl font-semibold mb-2">Results:</h3>
                    <p class="font-semibold">Best job order: ${data.best_order.join(', ')}</p>
                    <p class="font-semibold">Makespan: ${data.best_makespan}</p>
                    <h4 class="text-lg font-semibold mt-4 mb-2">All iterations:</h4>
                    <table class="w-full border-collapse">
                        <tr>
                            <th class="border border-gray-300 p-2">Iteration</th>
                            <th class="border border-gray-300 p-2">Job Order</th>
                            <th class="border border-gray-300 p-2">Makespan</th>
                        </tr>
                        ${data.all_orders.map(order => `
                            <tr>
                                <td class="border border-gray-300 p-2">${order.iteration}</td>
                                <td class="border border-gray-300 p-2">${order.order.join(', ')}</td>
                                <td class="border border-gray-300 p-2">${order.makespan}</td>
                            </tr>
                        `).join('')}
                    </table>
                `;
            }

            function displayExplanation(data) {
                explanationContainer.innerHTML = `
                    <h3 class="text-xl font-semibold mb-2">Explanation:</h3>
                    <ol class="list-decimal list-inside space-y-2">
                        <li>The CDS algorithm generates ${data.all_orders.length} two-machine subproblems.</li>
                        <li>For each subproblem:
                            <ul class="list-disc list-inside ml-4">
                                <li>The first virtual machine combines processing times from the first k machines.</li>
                                <li>The second virtual machine combines processing times from the last m-k machines.</li>
                                <li>Johnson's rule is applied to find an optimal job order for this subproblem.</li>
                            </ul>
                        </li>
                        <li>The makespan for each job order is calculated on the original problem.</li>
                        <li>The job order with the smallest makespan (${data.best_makespan}) is selected as the best solution.</li>
                        <li>This best order (${data.best_order.join(', ')}) is the final result of the CDS algorithm.</li>
                    </ol>
                    <p class="mt-2">The Gantt chart below visualizes the schedule using the best job order found.</p>
                `;
            }

            function createGanttChart(ganttData) {
                if (ganttChart) {
                    ganttChart.destroy();
                }

                const ctx = document.getElementById('gantt-chart').getContext('2d');
                const machines = [...new Set(ganttData.map(d => d.machine))];
                const jobs = [...new Set(ganttData.map(d => d.job))];
                const colors = generateColors(jobs.length);

                // Sort ganttData by start time
                ganttData.sort((a, b) => a.start - b.start);

                const datasets = jobs.map((job, jobIndex) => ({
                    label: job,
                    data: ganttData.filter(d => d.job === job).map(d => ({
                        x: [d.start, d.end],
                        y: d.machine,
                        duration: d.duration
                    })),
                    backgroundColor: colors[jobIndex],
                    barPercentage: 0.8
                }));

                ganttChart = new Chart(ctx, {
                    type: 'bar',
                    data: { datasets },
                    options: {
                        indexAxis: 'y',
                        scales: {
                            x: {
                                position: 'top',
                                title: { display: true, text: 'Time' },
                                stacked: true
                            },
                            y: {
                                title: { display: true, text: 'Machines' },
                                reverse: true
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: (context) => {
                                        const data = context.raw;
                                        return [
                                            `${context.dataset.label}`,
                                            `Start: ${data.x[0]}`,
                                            `End: ${data.x[1]}`,
                                            `Duration: ${data.duration}`
                                        ];
                                    }
                                }
                            },
                            legend: { position: 'bottom' },
                            title: {
                                display: true,
                                text: 'Gantt Chart - CDS Algorithm Schedule'
                            }
                        },
                        animation: {
                            onComplete: () => {
                                const chartInstance = ganttChart;
                                const ctx = chartInstance.ctx;
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'middle';
                                ctx.font = '12px Arial';
                                ctx.fillStyle = 'black';

                                chartInstance.data.datasets.forEach((dataset, datasetIndex) => {
                                    const meta = chartInstance.getDatasetMeta(datasetIndex);
                                    meta.data.forEach((bar, index) => {
                                        const data = dataset.data[index];
                                        ctx.fillText(dataset.label, bar.x + (bar.width / 2), bar.y);
                                    });
                                });
                            }
                        }
                    }
                });
            }

            function displayProcessingTimes(processingTimes) {
                const machines = processingTimes.length;
                const jobs = processingTimes[0].length;

                let html = '<h3 class="text-xl font-semibold mb-2">Processing Times:</h3>';
                html += '<table class="w-full border-collapse">';
                html += '<tr><th class="border border-gray-300 p-2"></th>';
                for (let j = 0; j < jobs; j++) {
                    html += `<th class="border border-gray-300 p-2">Job ${j + 1}</th>`;
                }
                html += '</tr>';
                for (let i = 0; i < machines; i++) {
                    html += `<tr><th class="border border-gray-300 p-2">Machine ${i + 1}</th>`;
                    for (let j = 0; j < jobs; j++) {
                        html += `<td class="border border-gray-300 p-2">${processingTimes[i][j]}</td>`;
                    }
                    html += '</tr>';
                }
                html += '</table>';

                processingTimesContainer.innerHTML = html;
            }

            function generateColors(n) {
                const colors = [];
                for (let i = 0; i < n; i++) {
                    colors.push(`hsl(${(i * 360) / n}, 70%, 60%)`);
                }
                return colors;
            }

            // Generate the initial matrix
            generateMatrix();
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)