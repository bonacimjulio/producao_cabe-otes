from flask import Flask, render_template, request, redirect, url_for, send_file
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from database import Database
import io

app = Flask(__name__)
db = Database()

OPERADORES = ["GILSON ROBERTO DE OLIVEIRA", "JÚLIO BONANCIM SILVA", "FELIPE DOMINGOS MOREIRA",
              "LUIZ HENRIQUE DE JESUS MARQUES", "RAFAEL BARROSO MARQUES", "JOÃO VITOR DA SILVA",
              "KEOLIN MIRELA FERRERA"]
MODELOS = ["Unidade Compressora 20+", "Unidade Compressora 15+", "Unidade Compressora 10 RED"]

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Producao_Detalhada')
    processed_data = output.getvalue()
    return processed_data

@app.route("/", methods=["GET"])
def home():
    period = request.args.get('period', 'hoje')
    start_date = None
    end_date = None
    period_name = ""
    today = datetime.now().date()

    if period == "hoje":
        start_date = today
        end_date = today
        period_name = "Hoje"
    elif period == "7dias":
        start_date = today - timedelta(days=6)
        end_date = today
        period_name = "Últimos 7 dias"
    elif period == "mes":
        start_date = today.replace(day=1)
        end_date = today
        period_name = "Este Mês"
    elif period == "completo":
        start_date = None
        end_date = None
        period_name = "Histórico Completo"
    
    start_str = start_date.strftime("%Y-%m-%d") if start_date else None
    end_str = end_date.strftime("%Y-%m-%d") if end_date else None

    stats = db.get_stats_periodo(start_str, end_str)
    registros = db.get_producao_periodo(start_str, end_str)
    producao_modelo = db.get_producao_por_modelo(start_str, end_str)
    
    # Geração dos gráficos Plotly
    plot_pie_html = ""
    plot_bar_html = ""
    if producao_modelo:
        df_pie = pd.DataFrame(producao_modelo, columns=['Modelo', 'Total'])
        fig_pie = px.pie(df_pie, names='Modelo', values='Total', hole=0.4)
        plot_pie_html = fig_pie.to_html(full_html=False)

        df_bar = pd.DataFrame(producao_modelo, columns=['Modelo', 'Total'])
        fig_bar = px.bar(df_bar, x='Modelo', y='Total', text_auto='.2s', color='Modelo')
        plot_bar_html = fig_bar.to_html(full_html=False)
    
    return render_template("index.html", 
                           operadores=OPERADORES, 
                           modelos=MODELOS, 
                           period_name=period_name,
                           stats=stats,
                           registros=registros,
                           plot_pie=plot_pie_html,
                           plot_bar=plot_bar_html,
                           start_date=start_str,
                           end_date=end_str)

@app.route("/register", methods=["POST"])
def register_production():
    modelo = request.form.get("modelo")
    op_montagem = request.form.get("op_montagem")
    qty_montado = int(request.form.get("qty_montado", 0))
    # ... Obter outros campos do formulário ...

    if not modelo or not any([qty_montado, ...]):
        # Se houver erro, renderizar a página novamente com uma mensagem
        return render_template("index.html", mensagem="Por favor, preencha todos os campos obrigatórios.", tipo_mensagem="warning")
    
    try:
        db.registrar_producao(modelo, op_montagem, qty_montado,
                              # ... passar outros valores ...
                             )
        return redirect(url_for("home", mensagem="Produção registrada com sucesso!", tipo_mensagem="success"))
    except Exception as e:
        return render_template("index.html", mensagem=f"Erro ao registrar: {e}", tipo_mensagem="danger")

@app.route("/download-excel")
def download_excel():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    registros = db.get_producao_periodo(start_date, end_date)

    if not registros:
        # Retorna uma resposta de erro ou uma página informativa
        return "Nenhum dado para exportar.", 404
    
    df_hist = pd.DataFrame(registros, columns=[
        "ID", "Modelo", "Op. Montagem", "Qtd. Montado", "Op. Pintura", "Qtd. Pintado",
        "Op. Teste", "Qtd. Testado", "Op. Retrabalho", "Qtd. Retrabalho", "Observação", "Data/Hora"
    ])
    excel_data = convert_df_to_excel(df_hist)
    
    return send_file(
        io.BytesIO(excel_data),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"producao_cabecotes_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )

# ... Adicionar outras rotas para excluir e limpar o histórico ...

if __name__ == "__main__":
    app.run(debug=True)