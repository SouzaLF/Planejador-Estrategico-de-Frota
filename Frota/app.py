import os
from flask import Flask, render_template, request, jsonify, send_from_directory
import math
from fpdf import FPDF
import base64
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Carrega variáveis de ambiente

app = Flask(__name__, template_folder='templates', static_folder='static')

class FleetAnalyzer:
    def __init__(self, vehicles, avg_load, deliveries_per_day, avg_km_route, cost_per_km_variable, revenue_per_delivery, 
                 fuel_consumption_km_l=3.5, fuel_emission_factor=2.68, fixed_cost_per_vehicle=100):
        self.vehicles = vehicles
        self.avg_load = avg_load
        self.deliveries_per_day = deliveries_per_day
        self.avg_km_route = avg_km_route
        self.cost_per_km_variable = cost_per_km_variable
        self.revenue_per_delivery = revenue_per_delivery
        self.fuel_consumption_km_l = fuel_consumption_km_l
        self.fuel_emission_factor = fuel_emission_factor
        self.fixed_cost_per_vehicle = fixed_cost_per_vehicle

    def calculate_kpis(self):
        total_capacity = self.vehicles * self.avg_load
        total_demand = self.deliveries_per_day * self.avg_load

        utilization = min(total_demand / total_capacity, 1) * 100 if total_capacity > 0 else 0
        idle_rate = max((total_capacity - total_demand) / total_capacity * 100, 0) if total_capacity > 0 else 0

        total_km = self.deliveries_per_day * self.avg_km_route

        # Cálculo de custo variável e custo fixo
        variable_cost = total_km * self.cost_per_km_variable
        fixed_cost = self.vehicles * self.fixed_cost_per_vehicle
        estimated_cost = variable_cost + fixed_cost
        cost_per_vehicle = estimated_cost / self.vehicles if self.vehicles > 0 else 0

        total_revenue = self.deliveries_per_day * self.revenue_per_delivery
        estimated_profit = total_revenue - estimated_cost

        # Emissões baseadas no consumo de combustível e fator de emissão
        total_fuel_consumed = total_km / self.fuel_consumption_km_l
        co2_emissions = total_fuel_consumed * self.fuel_emission_factor

        optimal_vehicles = math.ceil(total_demand / self.avg_load) if self.avg_load > 0 else 0

        return {
            'total_capacity': round(total_capacity, 2),
            'total_demand': round(total_demand, 2),
            'utilization': round(utilization, 1),
            'idle_rate': round(idle_rate, 1),
            'estimated_cost': round(estimated_cost, 2),
            'cost_per_vehicle': round(cost_per_vehicle, 2),
            'total_km': round(total_km, 2),
            'optimal_vehicles': optimal_vehicles,
            'total_revenue': round(total_revenue, 2),
            'estimated_profit': round(estimated_profit, 2),
            'co2_emissions': round(co2_emissions, 2),
            'efficiency_status': self.get_efficiency_status(utilization),
            'cost_status': self.get_cost_status(cost_per_vehicle),
            'profit_status': self.get_profit_status(estimated_profit),
            'emission_status': self.get_emission_status(co2_emissions)
        }
        
    def get_efficiency_status(self, utilization):
        if utilization >= 90:
            return {'status': 'Excelente', 'color': 'success', 'icon': 'bi-check-circle'}
        elif utilization >= 75:
            return {'status': 'Boa', 'color': 'info', 'icon': 'bi-check'}
        elif utilization >= 50:
            return {'status': 'Regular', 'color': 'warning', 'icon': 'bi-exclamation-triangle'}
        else:
            return {'status': 'Baixa', 'color': 'danger', 'icon': 'bi-exclamation-octagon'}
    
    def get_cost_status(self, cost_per_vehicle):
        if cost_per_vehicle < 200:
            return {'status': 'Ótimo', 'color': 'success', 'icon': 'bi-currency-dollar'}
        elif cost_per_vehicle < 400:
            return {'status': 'Aceitável', 'color': 'info', 'icon': 'bi-currency-dollar'}
        elif cost_per_vehicle < 600:
            return {'status': 'Alto', 'color': 'warning', 'icon': 'bi-currency-dollar'}
        else:
            return {'status': 'Muito Alto', 'color': 'danger', 'icon': 'bi-currency-dollar'}

    def get_profit_status(self, profit):
        if profit > 5000:
            return {'status': 'Excelente', 'color': 'success', 'icon': 'bi-graph-up'}
        elif profit > 2000:
            return {'status': 'Bom', 'color': 'info', 'icon': 'bi-graph-up'}
        elif profit > 0:
            return {'status': 'Positivo', 'color': 'warning', 'icon': 'bi-graph-up'}
        else:
            return {'status': 'Negativo', 'color': 'danger', 'icon': 'bi-graph-down'}

    def get_emission_status(self, emissions):
        if emissions < 100:
            return {'status': 'Baixa', 'color': 'success', 'icon': 'bi-tree'}
        elif emissions < 300:
            return {'status': 'Moderada', 'color': 'info', 'icon': 'bi-tree'}
        elif emissions < 500:
            return {'status': 'Alta', 'color': 'warning', 'icon': 'bi-tree'}
        else:
            return {'status': 'Muito Alta', 'color': 'danger', 'icon': 'bi-tree'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json

    try:
        vehicles = int(data['vehicles'])
        avg_load = float(data['avg_load'])
        deliveries_per_day = int(data['deliveries_per_day'])
        avg_km_route = float(data['avg_km_route'])
        cost_per_km = float(data['cost_per_km'])
        revenue_per_delivery = float(data['revenue_per_delivery'])

        analyzer = FleetAnalyzer(vehicles, avg_load, deliveries_per_day, avg_km_route, cost_per_km, revenue_per_delivery)
        results = analyzer.calculate_kpis()

        return jsonify({'success': True, 'results': results})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    data = request.json

    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Relatório de Análise de Frota", ln=1, align='C')
        pdf.set_font("Arial", size=12)
        pdf.ln(10)

        pdf.cell(200, 10, txt=f"Veículos: {data['vehicles']}", ln=1)
        pdf.cell(200, 10, txt=f"Entregas por dia: {data['deliveries_per_day']}", ln=1)
        pdf.ln(5)

        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Indicadores de Performance", ln=1)
        pdf.set_font("Arial", size=12)

        for kpi in data['kpis']:
            pdf.cell(200, 10, txt=f"{kpi['title']}: {kpi['value']}", ln=1)

        pdf.ln(10)
        pdf.cell(200, 10, txt=f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=1)

        pdf_output = pdf.output(dest='S').encode('latin1')
        return jsonify({'success': True, 'pdf': base64.b64encode(pdf_output).decode('latin1')})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("DEBUG", False))