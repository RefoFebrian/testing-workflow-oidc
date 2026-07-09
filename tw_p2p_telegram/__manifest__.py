# -*- coding: utf-8 -*-
{
    'name': "TW P2P with Telegram",

    'summary': "Module for P2P communication with Telegram notifications for user reminders",

    'description': """
        This module facilitates peer-to-peer (P2P) communication using Telegram. 
        It provides notifications for user reminders, ensuring that users are 
        promptly informed about important events and tasks. The integration 
        with Telegram allows for seamless and instant messaging, enhancing 
        user engagement and productivity.

        Specifically, this module is designed to remind users to confirm 
        transactions related to P2P purchase orders from ATPM to Main Dealer. 
        This ensures that all parties are aware of the transaction status and 
        can take necessary actions in a timely manner.
    """,

    'author': "Tunas Honda",
    'website': "https://www.honda-ku.com",

    'category': 'TW Purchase / TW Purchase',
    'version': '0.1',
    'license': 'LGPL-3',

    'depends': ['base','tw_p2p','tw_telegram'],

    'data': [
        'data/scheduled_actions.xml',
    ],
}

