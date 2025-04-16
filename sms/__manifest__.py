{
    'name': 'Orange Sonatel SMS',
    'version': '1.0',
    'author': 'ALHK-MMF',
    'category': 'CCBM/',
    'summary': 'Envoyer des SMS avec l\'API Orange Sonatel',
    'description': 'Ce module vous permet d\'envoyer des messages SMS depuis Odoo en utilisant l\'API Orange Sonatel.',
    'depends': ['orbit', 'calendar'],  # Add 'sms' here
    'data': [
        'security/ir.model.access.csv',
        # 'views/sms_config_view.xml',
        # 'views/send_sms_view.xml',
        # 'views/sms_history_view.xml',
        # 'views/test_orange_sms_view.xml',
        # 'views/sale_order_message_views.xml',
        # 'views/sale_order_view.xml',
        # 'views/menu_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}