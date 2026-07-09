{
    "name":"TW WIP Work Order",
    "version":"0.1",
    'license': 'AGPL-3',
    "author":"TDM",
    "category":"TDM",
    "description": """
        TW WIP Work Order
    """,
    "depends":['tw_work_order','tw_work_order_clocking'],
    "init_xml":[],
    "demo_xml":[],
    "data":[
        "security/res_groups.xml",
        "security/res_groups_button.xml",
        "security/ir.model.access.csv",
        
        "views/tw_work_order_wip_view.xml",
        "views/tw_menu.xml",
    ],
    "active":False,
    "installable":True
}
