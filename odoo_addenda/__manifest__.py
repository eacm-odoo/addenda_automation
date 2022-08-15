{
    'name': 'Automated Addendas',
    'sumary': 'Module to create addendas automatically',
    'description': """
        This new module helps anyone with some knowedge to create it's own custum addenda, whether is an expression addenda, or is build with tags or wants to edit the invoice xml

        FEATURES:
        -expression addenda
        -addenda created with tags(tree tag)
        -xml editor to preview what the user is building and visual guidance
        -add as many attributes as the user whats to a tag
        -edit the existing invoice xml(add new node or add logic to the attributes)
        -export in a zip file the addenda created with the whole module configurated
    """,
    'author': 'Odoo PS',
    'category': 'Accounting/Localizations/EDI',
    'version': '15.0.1.0.0',
    'depends': ['l10n_mx_edi'],
    'license': 'OPL-1',
    'data': [
        # views
        'views/addenda_menu_view.xml',
        'views/addenda_views.xml',
        'views/addenda_attribute_views.xml',
        'views/addenda_nodes_views.xml',
        'views/addenda_tag_views.xml',
        'views/ir_model_fields_form_views_inherit.xml',
        'views/addenda_conditional_views.xml',
        
        # security
        'security/ir.model.access.csv',

        # demo
        'demo/data.xml',
    ],
}
