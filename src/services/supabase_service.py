import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.supabase: Client = create_client(url, key)
    
    def create_order(self, order_data):
        """Criar um novo pedido no Supabase"""
        try:
            result = self.supabase.table('orders').insert(order_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erro ao criar pedido: {e}")
            return None
    
    def get_orders(self, status=None):
        """Buscar pedidos do Supabase"""
        try:
            query = self.supabase.table('orders').select('*')
            if status:
                query = query.eq('status', status)
            result = query.execute()
            return result.data
        except Exception as e:
            print(f"Erro ao buscar pedidos: {e}")
            return []
    
    def update_order_status(self, order_id, status):
        """Atualizar status do pedido"""
        try:
            result = self.supabase.table('orders').update({'status': status}).eq('id', order_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erro ao atualizar pedido: {e}")
            return None
    
    def mark_whatsapp_sent(self, order_id):
        """Marcar pedido como enviado para WhatsApp"""
        try:
            result = self.supabase.table('orders').update({'whatsapp_sent': True}).eq('id', order_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erro ao marcar WhatsApp enviado: {e}")
            return None
    
    def mark_vendor_notified(self, order_id):
        """Marcar vendedor como notificado"""
        try:
            result = self.supabase.table('orders').update({'vendor_notified': True}).eq('id', order_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Erro ao marcar vendedor notificado: {e}")
            return None
