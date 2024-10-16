from flask import Flask, render_template_string, request, jsonify, send_file
import numpy as np
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import logging

logging.basicConfig(level=logging.DEBUG)

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

def create_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Résultats de l'algorithme CDS", styles['Title']))
    elements.append(Spacer(1, 12))

    # Best order and makespan
    elements.append(Paragraph(f"Meilleur ordre des tâches: {', '.join(map(str, data['best_order']))}", styles['Normal']))
    elements.append(Paragraph(f"Makespan: {data['best_makespan']}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # All iterations table
    elements.append(Paragraph("Toutes les itérations:", styles['Heading2']))
    iterations_data = [['Itération', 'Ordre des tâches', 'Makespan']]
    for order in data['all_orders']:
        iterations_data.append([order['iteration'], ', '.join(map(str, order['order'])), order['makespan']])
    
    iterations_table = Table(iterations_data)
    iterations_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(iterations_table)
    elements.append(Spacer(1, 12))

    # Processing times table
    elements.append(Paragraph("Temps de traitement:", styles['Heading2']))
    processing_data = [[''] + [f'Tâche {j+1}' for j in range(len(data['processing_times'][0]))]]
    for i, row in enumerate(data['processing_times']):
        processing_data.append([f'Machine {i+1}'] + row)
    
    processing_table = Table(processing_data)
    processing_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(processing_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/download-pdf', methods=['POST'])
def download_pdf():
    try:
        data = request.json
        logging.debug(f"Received data for PDF: {data}")
        
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        pdf_buffer = create_pdf(data)
        
        response = send_file(
            pdf_buffer,
            as_attachment=True,
            download_name='resultats_cds.pdf',
            mimetype='application/pdf'
        )
        
        # Add headers to prevent caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        return jsonify({"error": str(e)}), 500

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
            'processing_times': processing_times.tolist()
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
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calculateur d'Algorithme CDS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-4xl font-bold text-center mb-8 text-indigo-600">
            <i class="fas fa-industry mr-2"></i>Calculateur d'Algorithme CDS
        </h1>
        <div class="bg-white rounded-lg shadow-md p-6">
            <div class="mb-6">
                <h2 class="text-2xl font-semibold mb-2">Qu'est-ce que l'algorithme CDS ?</h2>
                <p class="text-gray-700">L'algorithme de Campbell, Dudek et Smith (CDS) est une méthode heuristique pour résoudre les problèmes d'ordonnancement d'atelier à cheminement unique. Il génère une série de sous-problèmes à deux machines et applique la règle de Johnson à chacun, sélectionnant la meilleure solution globale.</p>
            </div>
            <div class="flex flex-wrap -mx-2 mb-4">
                <div class="w-full md:w-1/2 px-2 mb-4 md:mb-0">
                    <label for="machines" class="block text-sm font-medium text-gray-700 mb-1">Nombre de machines :</label>
                    <input type="number" id="machines" min="2" value="3" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
                <div class="w-full md:w-1/2 px-2">
                    <label for="jobs" class="block text-sm font-medium text-gray-700 mb-1">Nombre de tâches :</label>
                    <input type="number" id="jobs" min="2" value="4" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500">
                </div>
            </div>
            <button id="generate-matrix" class="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition duration-300 mb-4">
                <i class="fas fa-table mr-2"></i>Générer la Matrice
            </button>
            <div id="matrix-container" class="mb-4 overflow-x-auto"></div>
            <button id="calculate" class="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition duration-300">
                <i class="fas fa-calculator mr-2"></i>Appliquer l'Algorithme CDS
            </button>
            <div id="results" class="mt-6"></div>
            <div id="explanation" class="mt-6"></div>
            <div id="gantt-chart-container" class="mt-6">
                <canvas id="gantt-chart"></canvas>
            </div>
            <div id="processing-times" class="mt-6"></div>
            <button id="download-pdf" class="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-300">
                <i class="fas fa-file-pdf mr-2"></i>Télécharger les résultats en PDF
            </button>
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
                    html += `<th class="border border-gray-300 p-2">Tâche ${j + 1}</th>`;
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
                    <h3 class="text-xl font-semibold mb-2">Résultats :</h3>
                    <p class="font-semibold">Meilleur ordre des tâches : ${data.best_order.join(', ')}</p>
                    <p class="font-semibold">Makespan : ${data.best_makespan}</p>
                    <h4 class="text-lg font-semibold mt-4 mb-2">Toutes les itérations :</h4>
                    <table class="w-full border-collapse">
                        <tr>
                            <th class="border border-gray-300 p-2">Itération</th>
                            <th class="border border-gray-300 p-2">Ordre des tâches</th>
                            <th class="border border-gray-300 p-2">Makespan</th>
                        </tr>
                        ${data.all_orders.map(order => `
                            <tr class="${order.makespan === data.best_makespan ? 'bg-green-100' : ''}">
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
                    <h3 class="text-xl font-semibold mb-2">Explication :</h3>
                    <ol class="list-decimal list-inside space-y-2">
                        <li>L'algorithme CDS génère ${data.all_orders.length} sous-problèmes à deux machines.</li>
                        <li>Pour chaque sous-problème :
                            <ul class="list-disc list-inside ml-4">
                                <li>La première machine virtuelle combine les temps de traitement des k premières machines.</li>
                                <li>La seconde machine virtuelle combine les temps de traitement des m-k dernières machines.</li>
                                <li>La règle de Johnson est appliquée pour trouver un ordre optimal des tâches pour ce sous-problème.</li>
                            </ul>
                        </li>
                        <li>Le makespan pour chaque ordre des tâches est calculé sur le problème original.</li>
                        <li>L'ordre des tâches avec le plus petit makespan (${data.best_makespan}) est sélectionné comme la meilleure solution.</li>
                        <li>Cet ordre optimal (${data.best_order.join(', ')}) est le résultat final de l'algorithme CDS.</li>
                    </ol>
                    <p class="mt-2">Le diagramme de Gantt ci-dessous visualise l'ordonnancement en utilisant le meilleur ordre des tâches trouvé.</p>
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

                let html = '<h3 class="text-xl font-semibold mb-2">Temps de traitement :</h3>';
                html += '<table class="w-full border-collapse">';
                html += '<tr><th class="border border-gray-300 p-2"></th>';
                for (let j = 0; j < jobs; j++) {
                    html += `<th class="border border-gray-300 p-2">Tâche ${j + 1}</th>`;
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

            const downloadPdfBtn = document.getElementById('download-pdf');
            downloadPdfBtn.addEventListener('click', downloadPdf);

            function downloadPdf() {
                if (lastResults) {
                    fetch('/download-pdf', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(lastResults),
                    })
                    .then(response => response.blob())
                    .then(blob => {
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = 'resultats_cds.pdf';
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                    });
                }
            }
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)
