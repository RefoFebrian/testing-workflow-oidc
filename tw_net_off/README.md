# TW Journal Memorial Module

This module extends Odoo's accounting functionality by adding Journal Memorial management with approval workflow.

## Features

- Create and manage journal memorial entries
- Multi-level approval workflow
- Integration with accounting moves
- Branch-wise configuration
- Configurable approval settings

## Installation

1. Install the module using the Odoo app store or by placing it in your addons directory
2. Restart your Odoo server
3. Go to Apps and update the app list
4. Install the "TW Journal Memorial" module

## Configuration

1. Go to Accounting > Configuration > Settings > Journal Memorial Settings
2. Configure the following settings:
   - Enable/Disable approval requirement
   - Set default approver
   - Configure default journal

## Usage

### Creating a Journal Memorial

1. Go to Accounting > Journal Memorial > Journal Memorials
2. Click Create
3. Fill in the required fields:
   - Date
   - Reference (optional)
   - Branch
4. Add journal items:
   - Select Type (Debit/Credit)
   - Choose Account
   - Enter Amount
   - Add description
5. Click "Submit for Approval"

### Approving a Journal Memorial

1. Go to Accounting > Journal Memorial > Approvals
2. Select the journal memorial to approve
3. Click "Approve" or "Reject"

## Security

The module implements the following security groups:

- **Journal Memorial User**: Can create and manage their own journal memorials
- **Journal Memorial Approver**: Can approve/reject journal memorials
- **Journal Memorial Manager**: Full access to all journal memorial functionality

## Dependencies

- account
- tw_branch
- tw_account
- tw_approval (for approval workflow)

## Technical Notes

- The module follows Odoo 18 development standards
- All models use the `tw_` prefix
- Security is implemented following the principle of least privilege
- The code is documented following Odoo's coding guidelines

## License

This module is licensed under LGPL-3.
