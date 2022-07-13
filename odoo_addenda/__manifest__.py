{
    'name': 'Automated Addendas',
    'sumary': '',
    'description': """
        
    """,
    'author': 'Odoo PS',
    'category': 'Sales',
    'version': '15.0.1.0.0',
    'depends': ['sale', 'l10n_mx_edi'],
    'license': 'OPL-1',
    'data': [
        'views/addenda_menu_view.xml',
        'views/addenda_views.xml',
        'views/addenda_nodes_views.xml',
        'views/addenda_tag_views.xml',
        'views/res_partner_views_inherit.xml',
        'security/ir.model.access.csv',
    ],
}
