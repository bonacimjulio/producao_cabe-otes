# database.py (Versão corrigida e mais robusta)
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="producao.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        # A estrutura da tabela está correta
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS producao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                modelo TEXT,
                op_montagem TEXT,
                qty_montado INTEGER,
                op_pintura TEXT,
                qty_pintado INTEGER,
                op_teste TEXT,
                qty_testado INTEGER,
                op_retrabalho TEXT,
                qty_retrabalho INTEGER,
                observacao TEXT,
                timestamp TEXT
            )
        """)
        self.conn.commit()

    def registrar_producao(self, modelo, op_montagem, qty_montado, op_pintura, qty_pintado,
                           op_teste, qty_testado, op_retrabalho, qty_retrabalho, observacao):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            INSERT INTO producao (modelo, op_montagem, qty_montado, op_pintura, qty_pintado,
                                  op_teste, qty_testado, op_retrabalho, qty_retrabalho, observacao, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (modelo, op_montagem, qty_montado, op_pintura, qty_pintado, op_teste,
              qty_testado, op_retrabalho, qty_retrabalho, observacao, timestamp))
        self.conn.commit()

    def _build_where_clause(self, start_date, end_date):
        """Constrói a cláusula WHERE e os parâmetros para as datas."""
        if start_date and end_date:
            return "WHERE date(timestamp) BETWEEN ? AND ?", [start_date, end_date]
        return "", []

    def get_stats_periodo(self, start_date=None, end_date=None):
        where_clause, params = self._build_where_clause(start_date, end_date)
        query = f"""
            SELECT
                IFNULL(SUM(qty_montado), 0),
                IFNULL(SUM(qty_pintado), 0),
                IFNULL(SUM(qty_testado), 0),
                IFNULL(SUM(qty_retrabalho), 0)
            FROM producao {where_clause}
        """
        self.cursor.execute(query, params)
        result = self.cursor.fetchone()
        return {
            "total_montado": result[0],
            "total_pintado": result[1],
            "total_testado": result[2],
            "total_retrabalho": result[3]
        }

    def get_producao_por_modelo(self, start_date=None, end_date=None):
        # Lógica de consulta corrigida para ser mais segura
        conditions = ["qty_testado > 0"]
        params = []
        if start_date and end_date:
            conditions.append("date(timestamp) BETWEEN ? AND ?")
            params.extend([start_date, end_date])
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        query = f"SELECT modelo, SUM(qty_testado) FROM producao {where_clause} GROUP BY modelo"
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
        
    def get_producao_periodo(self, start_date=None, end_date=None):
        where_clause, params = self._build_where_clause(start_date, end_date)
        query = f"SELECT * FROM producao {where_clause} ORDER BY timestamp DESC"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_all_producao(self):
         return self.get_producao_periodo(None, None)

    def delete_producao_por_id(self, record_id):
        self.cursor.execute("DELETE FROM producao WHERE id = ?", (record_id,))
        self.conn.commit()

    def delete_all_producao(self):
        self.cursor.execute("DELETE FROM producao")
        self.conn.commit()