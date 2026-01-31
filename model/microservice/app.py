from flask import Flask, request, jsonify
import os
import json
import logging
from datetime import datetime
from models import ModelManager
from ab_test import ABTestManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.json.compact = False
app.json.sort_keys = False
model_manager = ModelManager()
ab_test_manager = ABTestManager()

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data or 'listing_id' not in data:
            return jsonify({"error": "Missing 'listing_id'"}), 400
        
        listing_id = data['listing_id']
        top_k = data.get('top_k', 3)
        
        model_variant = ab_test_manager.assign_variant(listing_id)
        result = model_manager.predict(listing_id, top_k, model_variant)
        
        if result is None:
            return jsonify({"error": f"No data for listing {listing_id}"}), 404
        
        ab_test_manager.log_interaction(
            listing_id, model_variant,
            result['top_aspects'], result['bottom_aspects']
        )
        
        response = {
            "listing_id": listing_id,
            "top_k": top_k,
            "top_aspects": result['top_aspects'],
            "bottom_aspects": result['bottom_aspects'],
            "chart_url": f"/predict/chart?listing_id={listing_id}",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Prediction: listing {listing_id}, model {model_variant}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/ab_stats', methods=['GET'])
def ab_stats():
    try:
        return jsonify(ab_test_manager.get_statistics())
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/ab_log', methods=['GET'])
def ab_log():
    try:
        variant = request.args.get('variant')
        limit = int(request.args.get('limit')) if request.args.get('limit') else None
        log_data = ab_test_manager.get_log(variant, limit)
        
        return jsonify({"total_records": len(log_data), "log": log_data})
    except Exception as e:
        logger.error(f"Log error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/feedback', methods=['POST'])
def feedback():
    try:
        data = request.get_json()
        if not data or 'listing_id' not in data or 'rating' not in data:
            return jsonify({"error": "Missing listing_id or rating"}), 400
        
        ab_test_manager.log_feedback(
            data['listing_id'], 
            data['rating'], 
            data.get('comment', '')
        )
        
        return jsonify({"status": "success"})
        
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/timeline', methods=['GET'])
def timeline():
    try:
        listing_id = request.args.get('listing_id')
        if not listing_id:
            return jsonify({"error": "Missing listing_id"}), 400
        
        return jsonify(model_manager.get_timeline_data(listing_id))
    except Exception as e:
        logger.error(f"Timeline error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/predict/chart', methods=['GET'])
def predict_chart():
    try:
        listing_id = request.args.get('listing_id')
        if not listing_id:
            return "<html><body><h1>Error</h1><p>Missing listing_id</p></body></html>", 400
        
        timeline_data = model_manager.get_timeline_data(listing_id)
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Timeline - Listing {{ listing_id }}</title>
            <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                    min-height: 100vh;
                }
                .container {
                    max-width: 1800px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    text-align: center;
                    margin-bottom: 10px;
                    font-size: 28px;
                }
                .stats {
                    text-align: center;
                    color: #666;
                    margin: 15px 0 30px 0;
                    font-size: 14px;
                }
                #chart {
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Timeline: Listing {{ listing_id }}</h1>
                
                <div class="stats">
                    Days: {{ total_days }} | Baseline total: {{ total_baseline }} | Advanced total: {{ total_advanced }}
                </div>
                
                <div id="chart"></div>
                
                <script>
                    var dates_baseline = {{ dates_baseline | safe }};
                    var counts_baseline = {{ counts_baseline | safe }};
                    var dates_advanced = {{ dates_advanced | safe }};
                    var counts_advanced = {{ counts_advanced | safe }};
                    var scores_baseline = {{ scores_baseline | safe }};
                    var scores_advanced = {{ scores_advanced | safe }};
                    
                    // Calculate cumulative sums
                    function cumsum(arr) {
                        var result = [];
                        var sum = 0;
                        for (var i = 0; i < arr.length; i++) {
                            sum += arr[i];
                            result.push(sum);
                        }
                        return result;
                    }
                    
                    var cumulative_baseline = cumsum(counts_baseline);
                    var cumulative_advanced = cumsum(counts_advanced);
                    
                    // Cumulative aspects traces
                    var trace_cumulative_baseline = {
                        x: dates_baseline,
                        y: cumulative_baseline,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Baseline (TF-IDF)',
                        line: {color: '#3498db', width: 2.5, shape: 'hv'},
                        fill: 'tozeroy',
                        fillcolor: 'rgba(52, 152, 219, 0.2)',
                        xaxis: 'x',
                        yaxis: 'y',
                        hovertemplate: '<b>%{x}</b><br>Cumulative: %{y}<extra></extra>'
                    };
                    
                    var trace_cumulative_advanced = {
                        x: dates_advanced,
                        y: cumulative_advanced,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Advanced (Embeddings)',
                        line: {color: '#e74c3c', width: 2.5, shape: 'hv'},
                        fill: 'tozeroy',
                        fillcolor: 'rgba(231, 76, 60, 0.2)',
                        xaxis: 'x2',
                        yaxis: 'y2',
                        hovertemplate: '<b>%{x}</b><br>Cumulative: %{y}<extra></extra>'
                    };
                    
                    // Score traces
                    var trace_score_baseline = {
                        x: dates_baseline,
                        y: scores_baseline,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Baseline Score',
                        line: {color: '#3498db', width: 2, shape: 'hv'},
                        fill: 'tozeroy',
                        fillcolor: 'rgba(52, 152, 219, 0.15)',
                        xaxis: 'x3',
                        yaxis: 'y3',
                        hovertemplate: '<b>%{x}</b><br>Score: %{y}<extra></extra>'
                    };
                    
                    var trace_score_advanced = {
                        x: dates_advanced,
                        y: scores_advanced,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Advanced Score',
                        line: {color: '#e74c3c', width: 2, shape: 'hv'},
                        fill: 'tozeroy',
                        fillcolor: 'rgba(231, 76, 60, 0.15)',
                        xaxis: 'x4',
                        yaxis: 'y4',
                        hovertemplate: '<b>%{x}</b><br>Score: %{y}<extra></extra>'
                    };
                    
                    var layout = {
                        grid: {rows: 4, columns: 1, pattern: 'independent', roworder: 'top to bottom'},
                        height: 1200,
                        showlegend: false,
                        margin: {l: 60, r: 40, t: 20, b: 60},
                        
                        // Cumulative Baseline
                        xaxis: {
                            title: 'Date',
                            showgrid: true,
                            gridcolor: '#e0e0e0'
                        },
                        yaxis: {
                            title: 'Cumulative Aspects (Baseline)',
                            showgrid: true,
                            gridcolor: '#e0e0e0'
                        },
                        
                        // Cumulative Advanced
                        xaxis2: {
                            title: 'Date',
                            showgrid: true,
                            gridcolor: '#e0e0e0'
                        },
                        yaxis2: {
                            title: 'Cumulative Aspects (Advanced)',
                            showgrid: true,
                            gridcolor: '#e0e0e0'
                        },
                        
                        // Score Baseline
                        xaxis3: {
                            title: 'Date',
                            showgrid: true,
                            gridcolor: '#e0e0e0'
                        },
                        yaxis3: {
                            title: 'Score (Baseline)',
                            showgrid: true,
                            gridcolor: '#e0e0e0',
                            zeroline: true,
                            zerolinecolor: '#999',
                            zerolinewidth: 2
                        },
                        
                        // Score Advanced
                        xaxis4: {
                            title: 'Date',
                            showgrid: true,
                            gridcolor: '#e0e0e0'
                        },
                        yaxis4: {
                            title: 'Score (Advanced)',
                            showgrid: true,
                            gridcolor: '#e0e0e0',
                            zeroline: true,
                            zerolinecolor: '#999',
                            zerolinewidth: 2
                        },
                        
                        plot_bgcolor: '#fafafa',
                        paper_bgcolor: 'white'
                    };
                    
                    var config = {
                        responsive: true,
                        displayModeBar: true,
                        displaylogo: false,
                        modeBarButtonsToRemove: ['lasso2d', 'select2d']
                    };
                    
                    Plotly.newPlot('chart', 
                        [trace_cumulative_baseline, trace_cumulative_advanced, trace_score_baseline, trace_score_advanced], 
                        layout, 
                        config
                    );
                </script>
            </div>
        </body>
        </html>
        """
        
        baseline = timeline_data['baseline']
        advanced = timeline_data['advanced']
        
        template_vars = {
            'listing_id': listing_id,
            'total_days': max(len(baseline['dates']), len(advanced['dates'])) if baseline['dates'] or advanced['dates'] else 0,
            'total_baseline': sum(baseline['counts']) if baseline['counts'] else 0,
            'total_advanced': sum(advanced['counts']) if advanced['counts'] else 0,
            'dates_baseline': json.dumps(baseline['dates']),
            'counts_baseline': json.dumps(baseline['counts']),
            'scores_baseline': json.dumps(baseline['scores']),
            'dates_advanced': json.dumps(advanced['dates']),
            'counts_advanced': json.dumps(advanced['counts']),
            'scores_advanced': json.dumps(advanced['scores'])
        }
        
        html = html_template
        for key, value in template_vars.items():
            html = html.replace('{{ ' + key + ' | safe }}', str(value))
            html = html.replace('{{ ' + key + ' }}', str(value))
        
        return html
        
    except Exception as e:
        logger.error(f"Chart error: {str(e)}")
        return f"<html><body><h1>Error</h1><pre>{str(e)}</pre></body></html>", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)