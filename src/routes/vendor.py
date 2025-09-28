from flask import Blueprint, request, jsonify
from src.services.supabase_service import SupabaseService
from datetime import datetime

vendor_bp = Blueprint('vendor', __name__)

@vendor_bp.route('/vendor/orders', methods=['GET'])
def get_vendor_orders():
    """Buscar pedidos para o painel do vendedor via Supabase"""
    try:
        supabase_service = SupabaseService()
        
        # Filtros opcionais
        status = request.args.get('status')
        
        orders = supabase_service.get_orders(status)
        
        return jsonify({
            'orders': orders,
            'total': len(orders),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendor_bp.route('/vendor/orders/<order_id>/status', methods=['PUT'])
def update_vendor_order_status(order_id):
    """Atualizar status do pedido via Supabase"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status é obrigatório'}), 400
        
        valid_statuses = ['pending', 'confirmed', 'preparing', 'ready', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Status inválido. Use: {", ".join(valid_statuses)}'}), 400
        
        supabase_service = SupabaseService()
        updated_order = supabase_service.update_order_status(order_id, new_status)
        
        if updated_order:
            return jsonify({
                'message': 'Status atualizado com sucesso',
                'order': updated_order
            }), 200
        else:
            return jsonify({'error': 'Falha ao atualizar pedido'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vendor_bp.route('/vendor/orders/stats', methods=['GET'])
def get_vendor_stats():
    """Obter estatísticas dos pedidos para o vendedor"""
    try:
        supabase_service = SupabaseService()
        
        # Buscar todos os pedidos
        all_orders = supabase_service.get_orders()
        
        # Contar por status
        stats = {}
        for order in all_orders:
            status = order.get('status', 'unknown')
            if status not in stats:
                stats[status] = 0
            stats[status] += 1
        
        # Pedidos de hoje (aproximação - seria melhor filtrar no Supabase)
        today = datetime.now().date()
        today_orders = [order for order in all_orders 
                       if order.get('order_date', '').startswith(today.strftime('%Y-%m-%d'))]
        
        return jsonify({
            'stats': stats,
            'total_orders': len(all_orders),
            'today_orders': len(today_orders),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
