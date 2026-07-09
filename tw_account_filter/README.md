# Account Filter Module

This module provides account filtering functionality for Tunas Group's Odoo implementation.

## Features

- Define account filters based on account type, prefix, and user type
- Easy integration with other modules for account filtering
- Role-based access control for managing account filters

## Installation

1. Copy the `tw_account_filter` directory to your Odoo addons directory
2. Install the module through the Odoo Apps interface or using the command line:
   ```
   python odoo-bin -d your_database -i tw_account_filter --stop-after-init
   ```

## Configuration

1. Go to Accounting > Configuration > Account Filters
2. Create a new filter by clicking "Create"
3. Fill in the filter details:
   - Reference/Description: Select the filter type
   - Prefix: Enter the account code prefix to filter
   - Internal Type: Select the account type
   - Account Type: Select the user type

## Usage

This module is primarily used by other modules to filter accounts based on predefined criteria. The main method used is:

```python
domain = self.env['tw.account.filter'].get_domain_account(filter_name)
```

## Security

Access to account filters is controlled by the following security groups:

- **Account Filter Read**: Can view account filters
- **Account Filter Update**: Can create and modify account filters
- **Account Filter Delete**: Can delete account filters

## Dependencies

- account
- tw_branch
- tw_dealer_menu

## License

This module is licensed under LGPL-3.

## Author

- Tunas Group
