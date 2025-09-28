import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

class WhatsAppService:
    def __init__(self):
        self.phone_number = os.getenv("WHATSAPP_PHONE_NUMBER")
        if not self.phone_number:
            raise ValueError("WHATSAPP_PHONE_NUMBER must be set in environment variables")
    
    def format_order_message(self, order_data):
        """Formatar mensagem do pedido para WhatsApp"""
        items_text = ""
        for item in order_data.get('items', []):
            items_text += f"• {item.get('name', 'Item')} - Qtd: {item.get('quantity', 1)} - R$ {item.get('price', 0):.2f}\n"
        
        message = f"""🍽️ *NOVO PEDIDO - Mesa e Sabores*

📋 *Pedido ID:* {order_data.get('id', 'N/A')}
📅 *Data:* {order_data.get('order_date', 'N/A')}

🛒 *Itens do Pedido:*
{items_text}
💰 *Total:* R$ {order_data.get('total_amount', 0):.2f}

📱 *Status:* {order_data.get('status', 'Pendente')}

---
Mesa e Sabores - Sistema de Pedidos"""
        
        return message
    
    def send_order_notification(self, order_data):
        """Enviar notificação do pedido via WhatsApp Web"""
        try:
            message = self.format_order_message(order_data)
            encoded_message = quote(message)
            whatsapp_url = f"https://wa.me/{self.phone_number}?text={encoded_message}"
            
            # Retorna a URL para ser aberta pelo frontend
            return {
                'success': True,
                'whatsapp_url': whatsapp_url,
                'message': 'URL do WhatsApp gerada com sucesso'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Erro ao gerar URL do WhatsApp'
            }
