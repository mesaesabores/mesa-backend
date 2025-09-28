from flask import Blueprint, request, jsonify
from src.models import db
from src.models.order import Order
from src.services.supabase_service import SupabaseService
from src.services.whatsapp_service import WhatsAppService
from datetime import datetime
import urllib.parse
import uuid

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/orders', methods=['POST'])
def create_order():
    """Criar um novo pedido"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        required_fields = ['customer_name', 'customer_whatsapp', 'customer_address', 'payment_method', 'items', 'total_price']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Criar novo pedido no banco local (SQLite)
        order = Order(
            customer_name=data['customer_name'],
            customer_whatsapp=data['customer_whatsapp'],
            customer_address=data['customer_address'],
            payment_method=data['payment_method'],
            items=data['items'],
            total_price=data['total_price']
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Integração com Supabase
        try:
            supabase_service = SupabaseService()
            supabase_order_data = {
                'items': data['items'],
                'total_amount': data['total_price'],
                'status': 'pending',
                'user_id': None  # Pode ser implementado sistema de usuários depois
            }
            supabase_order = supabase_service.create_order(supabase_order_data)
            
            if supabase_order:
                # Gerar URL do WhatsApp
                whatsapp_service = WhatsAppService()
                whatsapp_data = {
                    'id': supabase_order.get('id', order.id),
                    'items': data['items'],
                    'total_amount': data['total_price'],
                    'status': 'pending',
                    'order_date': datetime.now().strftime('%d/%m/%Y %H:%M')
                }
                whatsapp_result = whatsapp_service.send_order_notification(whatsapp_data)
                
                # Marcar como enviado para WhatsApp se bem-sucedido
                if whatsapp_result.get('success'):
                    supabase_service.mark_whatsapp_sent(supabase_order['id'])
                    supabase_service.mark_vendor_notified(supabase_order['id'])
                
                return jsonify({
                    'message': 'Pedido criado com sucesso',
                    'order': order.to_dict(),
                    'supabase_order_id': supabase_order.get('id'),
                    'whatsapp_url': whatsapp_result.get('whatsapp_url') if whatsapp_result.get('success') else None,
                    'whatsapp_success': whatsapp_result.get('success', False)
                }), 201
            else:
                return jsonify({
                    'message': 'Pedido criado localmente, mas falha na integração com Supabase',
                    'order': order.to_dict()
                }), 201
                
        except Exception as supabase_error:
            print(f"Erro na integração Supabase: {supabase_error}")
            return jsonify({
                'message': 'Pedido criado localmente, mas falha na integração com Supabase',
                'order': order.to_dict(),
                'supabase_error': str(supabase_error)
            }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders', methods=['GET'])
def get_orders():
    """Listar todos os pedidos"""
    try:
        # Filtros opcionais
        status = request.args.get('status')
        date = request.args.get('date')
        
        query = Order.query
        
        if status:
            query = query.filter(Order.status == status)
        
        if date:
            # Filtrar por data específica
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                query = query.filter(db.func.date(Order.created_at) == date_obj)
            except ValueError:
                return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        # Ordenar por data de criação (mais recentes primeiro)
        orders = query.order_by(Order.created_at.desc()).all()
        
        return jsonify({
            'orders': [order.to_dict() for order in orders],
            'total': len(orders)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Obter um pedido específico"""
    try:
        order = Order.query.get_or_404(order_id)
        return jsonify({'order': order.to_dict()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Atualizar o status de um pedido"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status é obrigatório'}), 400
        
        valid_statuses = ['received', 'paid', 'preparing', 'ready', 'delivering', 'delivered']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Status inválido. Use: {", ".join(valid_statuses)}'}), 400
        
        order = Order.query.get_or_404(order_id)
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Status atualizado com sucesso',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders/<int:order_id>/whatsapp-message', methods=['GET'])
def generate_whatsapp_message(order_id):
    """Gerar mensagem do WhatsApp para notificar o cliente sobre mudança de status"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Gerar mensagem baseada no status atual
        status_messages = {
            'received': f'🍽️ *Mesa e Sabores*\n\nOlá {order.customer_name}!\n\n✅ Seu pedido foi recebido com sucesso!\n\n📋 *Pedido #{order.id}*\n💰 Total: R$ {order.total_price:.2f}\n\nEm breve entraremos em contato para confirmar o pagamento.\n\nObrigado pela preferência! 😊',
            
            'paid': f'🍽️ *Mesa e Sabores*\n\nOlá {order.customer_name}!\n\n💳 Pagamento confirmado!\n\n📋 *Pedido #{order.id}*\n✅ Seu pedido já está sendo preparado com muito carinho.\n\nTempo estimado: 30-45 minutos\n\nObrigado! 😊',
            
            'preparing': f'🍽️ *Mesa e Sabores*\n\nOlá {order.customer_name}!\n\n👨‍🍳 Seu pedido está sendo preparado!\n\n📋 *Pedido #{order.id}*\n🔥 Nossa equipe está caprichando no seu prato.\n\nTempo estimado: 20-30 minutos\n\nAguarde, está ficando delicioso! 😋',
            
            'ready': f'🍽️ *Mesa e Sabores*\n\nOlá {order.customer_name}!\n\n🎉 Seu pedido está pronto!\n\n📋 *Pedido #{order.id}*\n📍 Endereço: {order.customer_address}\n\nNosso entregador sairá em breve para levar seu pedido quentinho! 🚗\n\nObrigado pela paciência! 😊',
            
            'delivering': f'🍽️ *Mesa e Sabores*\n\nOlá {order.customer_name}!\n\n🚗 Seu pedido saiu para entrega!\n\n📋 *Pedido #{order.id}*\n📍 Destino: {order.customer_address}\n\nNosso entregador está a caminho. Tempo estimado: 15-20 minutos.\n\nPrepare-se para saborear! 😋',
            
            'delivered': f'🍽️ *Mesa e Sabores*\n\nOlá {order.customer_name}!\n\n✅ Pedido entregue com sucesso!\n\n📋 *Pedido #{order.id}*\n\nEsperamos que tenha gostado da sua refeição! 😋\n\nSua opinião é muito importante para nós. Avalie nosso atendimento!\n\nObrigado pela preferência! ❤️'
        }
        
        message = status_messages.get(order.status, f'Atualização do pedido #{order.id}: {Order.get_status_display(order.status)}')
        encoded_message = urllib.parse.quote(message)
        whatsapp_url = f'https://wa.me/{order.customer_whatsapp}?text={encoded_message}'
        
        return jsonify({
            'message': message,
            'whatsapp_url': whatsapp_url,
            'customer_whatsapp': order.customer_whatsapp,
            'status': order.status,
            'status_display': Order.get_status_display(order.status)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/orders/stats', methods=['GET'])
def get_order_stats():
    """Obter estatísticas dos pedidos"""
    try:
        # Contar pedidos por status
        stats = {}
        statuses = ['received', 'paid', 'preparing', 'ready', 'delivering', 'delivered']
        
        for status in statuses:
            count = Order.query.filter(Order.status == status).count()
            stats[status] = {
                'count': count,
                'display': Order.get_status_display(status)
            }
        
        # Total de pedidos
        total_orders = Order.query.count()
        
        # Pedidos de hoje
        today = datetime.now().date()
        today_orders = Order.query.filter(db.func.date(Order.created_at) == today).count()
        
        return jsonify({
            'stats': stats,
            'total_orders': total_orders,
            'today_orders': today_orders
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

