from flask import Flask, render_template_string, request, jsonify
import numpy as np

app = Flask(__name__)

# Your existing functions
def johnson(P):
    ordre1 = []
    ordre2 = []
    U = []
    V = []

    for i in range(1, len(P)):
        for j in range(len(P[i])):
            if P[i-1][j] < P[i][j]:
                ordre1.append(j)
                U.append(P[i-1][j])
            if P[i-1][j] >= P[i][j]:
                ordre2.append(j)
                V.append(P[i][j])
    
    L = sorted(zip(U, ordre1), key=lambda x: x[0])
    L = list(zip(*L))
    T = sorted(zip(V, ordre2), key=lambda x: x[0], reverse=True)
    T = list(zip(*T))
    ordre = list(L[1]) + list(T[1])
    return ordre

def makespan(P, ordre):
    C = [[0 for _ in range(len(P[0]))] for _ in range(len(P))]
    C[0][ordre[0]] = P[0][ordre[0]]
    C[1][ordre[0]] = C[0][ordre[0]] + P[1][ordre[0]]
    for i in range(len(P)-1):
        for j in range(1, len(P[i])):
            C[i][ordre[j]] = C[i][ordre[j-1]] + P[i][ordre[j]]
    for i in range(1, len(P)):
        for j in range(1, len(P[i])):
            C[i][ordre[j]] = max(C[i-1][ordre[j]], C[i][ordre[j-1]]) + P[i][ordre[j]]
    Cmax = max(max(row) for row in C)
    return C, Cmax

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.json
        P = data['matrix']
        ordre = johnson(P)
        C, Cmax = makespan(P, ordre)
        return jsonify({
            'ordre': ordre,
            'Cmax': Cmax,
            'C': C
        })
    return render_template_string(HTML_TEMPLATE)

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Makespan Calculator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-4xl font-bold text-center mb-8 text-indigo-600">
            <i class="fas fa-industry mr-2"></i>Makespan Calculator
        </h1>
        <div class="bg-white rounded-lg shadow-md p-6">
            <div class="mb-6">
                <h2 class="text-2xl font-semibold mb-2">What is Makespan?</h2>
                <p class="text-gray-700">Makespan is the total length of the schedule for a set of jobs. It's the time difference between the start of the first job and the completion of the last job in the schedule.</p>
            </div>
            <div class="flex flex-wrap -mx-2 mb-4">
                <div class="w-full md:w-1/2 px-2 mb-4 md:mb-0">
                    <label for="rows" class="block text-sm font-medium text-gray-700 mb-1">Number of machines:</label>
                    <input type="number" id="rows" min="2" value="2" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="w-full md:w-1/2 px-2">
                    <label for="cols" class="block text-sm font-medium text-gray-700 mb-1">Number of jobs:</label>
                    <input type="number" id="cols" min="1" value="8" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
            </div>
            <button id="generate-matrix" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-300 mb-4">
                <i class="fas fa-table mr-2"></i>Generate Matrix
            </button>
            <div id="matrix-container" class="mb-4 overflow-x-auto"></div>
            <button id="calculate" class="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-300">
                <i class="fas fa-calculator mr-2"></i>Calculate Makespan
            </button>
            <div id="results" class="mt-6"></div>
            <div id="explanation" class="mt-6"></div>
            <div id="chart-container" class="mt-6">
                <canvas id="gantt-chart"></canvas>
            </div>
        </div>
    </div>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const generateMatrixBtn = document.getElementById('generate-matrix');
            const calculateBtn = document.getElementById('calculate');
            const matrixContainer = document.getElementById('matrix-container');
            const resultsContainer = document.getElementById('results');
            const explanationContainer = document.getElementById('explanation');
            const chartContainer = document.getElementById('chart-container');
            let ganttChart = null;

            generateMatrixBtn.addEventListener('click', generateMatrix);
            calculateBtn.addEventListener('click', calculateMakespan);

            function generateMatrix() {
                const rows = parseInt(document.getElementById('rows').value);
                const cols = parseInt(document.getElementById('cols').value);

                let html = '<table class="w-full border-collapse">';
                html += '<tr><th class="border border-gray-300 p-2"></th>';
                for (let j = 0; j < cols; j++) {
                    html += `<th class="border border-gray-300 p-2">Job ${j + 1}</th>`;
                }
                html += '</tr>';
                for (let i = 0; i < rows; i++) {
                    html += `<tr><th class="border border-gray-300 p-2">Machine ${i + 1}</th>`;
                    for (let j = 0; j < cols; j++) {
                        html += `<td class="border border-gray-300 p-2">
                            <input type="number" id="cell-${i}-${j}" min="0" value="0" 
                            class="w-full px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                        </td>`;
                    }
                    html += '</tr>';
                }
                html += '</table>';

                matrixContainer.innerHTML = html;
            }

            function calculateMakespan() {
                const rows = parseInt(document.getElementById('rows').value);
                const cols = parseInt(document.getElementById('cols').value);
                let matrix = [];

                for (let i = 0; i < rows; i++) {
                    let row = [];
                    for (let j = 0; j < cols; j++) {
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
                    resultsContainer.innerHTML = `
                        <h3 class="text-xl font-semibold mb-2">Results:</h3>
                        <p class="font-semibold">Optimal job order: ${data.ordre.map(j => j + 1).join(', ')}</p>
                        <p class="font-semibold">Makespan (Cmax): ${data.Cmax}</p>
                        <p class="font-semibold mt-4">Time matrix:</p>
                        <pre class="bg-gray-100 p-4 rounded-md overflow-x-auto">${JSON.stringify(data.C, null, 2)}</pre>
                    `;
                    explanationContainer.innerHTML = `
                        <h3 class="text-xl font-semibold mb-2">Explanation:</h3>
                        <ol class="list-decimal list-inside space-y-2">
                            <li>The Johnson's algorithm is applied to find the optimal job order.</li>
                            <li>Jobs are scheduled according to this order on each machine.</li>
                            <li>The completion time for each job on each machine is calculated.</li>
                            <li>The makespan is the maximum completion time across all jobs and machines.</li>
                        </ol>
                    `;
                    createGanttChart(data.C, data.ordre);
                });
            }

            function createGanttChart(C, ordre) {
                if (ganttChart) {
                    ganttChart.destroy();
                }

                const ctx = document.getElementById('gantt-chart').getContext('2d');
                const datasets = C.map((row, machineIndex) => {
                    return {
                        label: `Machine ${machineIndex + 1}`,
                        data: ordre.map(jobIndex => {
                            const start = machineIndex > 0 ? C[machineIndex - 1][jobIndex] : 0;
                            const duration = C[machineIndex][jobIndex] - start;
                            return {
                                x: [start, C[machineIndex][jobIndex]],
                                y: `Job ${jobIndex + 1}`,
                                duration: duration
                            };
                        }),
                        backgroundColor: `hsl(${machineIndex * 360 / C.length}, 70%, 60%)`,
                        barPercentage: 0.5
                    };
                });

                ganttChart = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        datasets: datasets
                    },
                    options: {
                        indexAxis: 'y',
                        scales: {
                            x: {
                                position: 'top',
                                title: {
                                    display: true,
                                    text: 'Time'
                                }
                            },
                            y: {
                                title: {
                                    display: true,
                                    text: 'Jobs'
                                }
                            }
                        },
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const data = context.raw;
                                        return `${context.dataset.label}: Start: ${data.x[0]}, End: ${data.x[1]}, Duration: ${data.duration}`;
                                    }
                                }
                            },
                            legend: {
                                position: 'bottom'
                            },
                            title: {
                                display: true,
                                text: 'Gantt Chart of Job Schedule'
                            }
                        }
                    }
                });
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