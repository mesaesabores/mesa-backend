from src.models import db
from datetime import datetime
import json

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_whatsapp = db.Column(db.String(20), nullable=False)
    customer_address = db.Column(db.Text, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # 'pix' or 'credit_card'
    items = db.Column(db.Text, nullable=False)  # JSON string with order items
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='received')  # received, paid, preparing, ready, delivering, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, customer_name, customer_whatsapp, customer_address, payment_method, items, total_price):
        self.customer_name = customer_name
        self.customer_whatsapp = customer_whatsapp
        self.customer_address = customer_address
        self.payment_method = payment_method
        self.items = json.dumps(items) if isinstance(items, (list, dict)) else items
        self.total_price = total_price
    
    def get_items(self):
        """Retorna os itens do pedido como objeto Python"""
        return json.loads(self.items) if self.items else []
    
    def to_dict(self):
        """Converte o pedido para dicionário"""
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_whatsapp': self.customer_whatsapp,
            'customer_address': self.customer_address,
            'payment_method': self.payment_method,
            'items': self.get_items(),
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_status_display(status):
        """Retorna o nome amigável do status"""
        status_map = {
            'received': 'Pedido Recebido',
            'paid': 'Pagamento Confirmado',
            'preparing': 'Em Preparo',
            'ready': 'Pronto para Entrega',
            'delivering': 'Saiu para Entrega',
            'delivered': 'Entregue'
        }
        return status_map.get(status, status)
    
    @staticmethod
    def get_next_status(current_status):
        """Retorna o próximo status na sequência"""
        status_flow = {
            'received': 'paid',
            'paid': 'preparing',
            'preparing': 'ready',
            'ready': 'delivering',
            'delivering': 'delivered'
        }
        return status_flow.get(current_status)

