# TW Lead Module - Test Suite

This directory contains comprehensive test suites for the `tw_lead` module.

## Test Files

### 1. `test_tw_lead.py`
Main test file for the `tw.lead` model with 28 test cases covering:

- **Basic CRUD Operations**: Lead creation, updates, and deletion prevention
- **Field Validations**:
  - Identification number validation (16 digits, no leading zero)
  - Birthdate validation (minimum age 17 years)
  - Email validation (proper format)
  - Phone number validation (numeric only)
  - Mobile number formatting (auto-add +62 country code)
- **Computed Fields**: Interest, name generation, unit availability
- **State Transitions**: Open → Dealt → Proposed → Approved workflow
- **Actions**: Deal, Propose, Reject, Approve
- **Partner Synchronization**: Creating and updating partner records
- **Address Synchronization**: KTP and domicile address handling
- **Business Logic**: OTR price validation, down payment rules, duplicate ID prevention

### 2. `test_tw_lead_addresses.py`
Tests for the `tw.lead.addresses` model with 12 test cases:

- Address creation and auto-naming
- Single KTP address constraint per lead
- Multiple non-KTP addresses support
- Address field cascading (state → city → district → sub-district)
- Zip code auto-population from sub-district
- Address type computation
- Lead relationship validation

### 3. `test_tw_lead_documents.py`
Tests for the `tw.lead.documents` model with 12 test cases:

- Document creation with and without files
- Document name auto-generation
- File upload and storage
- Filename convention (tw_lead-{type}-{lead_id}.{ext})
- Multiple documents per lead
- Different file extensions support
- Upload date tracking
- Document display computation

### 4. `test_tw_lead_logs.py`
Tests for the `tw.lead.logs` model with 13 test cases:

- Log creation and required fields
- Auto datetime stamping
- Multiple logs per lead
- Log ordering by date (ascending)
- Automatic log creation on state changes:
  - Deal action
  - Propose action
  - Reject action
  - Approve action
- Custom log entries
- Category relationship

### 5. `common.py`
Common utilities and base classes for reducing test code duplication.

## Running the Tests

### Run all tw_lead tests:
```bash
odoo-bin -c /path/to/config.conf -d test_database --test-tags=tw_lead --stop-after-init
```

### Run specific test file:
```bash
odoo-bin -c /path/to/config.conf -d test_database --test-tags=tw_lead.test_tw_lead --stop-after-init
```

### Run specific test class:
```bash
odoo-bin -c /path/to/config.conf -d test_database --test-tags=tw_lead.test_tw_lead.TestTwLead --stop-after-init
```

### Run specific test method:
```bash
odoo-bin -c /path/to/config.conf -d test_database --test-tags=tw_lead.test_tw_lead.TestTwLead.test_01_create_lead_basic --stop-after-init
```

## Test Coverage

The test suite covers:
- ✅ Model validations and constraints
- ✅ Field computations and defaults
- ✅ Onchange methods
- ✅ State workflows and transitions
- ✅ CRUD operations (Create, Read, Update, Delete prevention)
- ✅ Partner synchronization
- ✅ Address management
- ✅ Document handling
- ✅ Audit logs
- ✅ Business rules and logic

## Test Tags

All tests are tagged with:
- `post_install`: Run after module installation
- `-at_install`: Do not run during installation
- `tw_lead`: Module-specific tag

## Prerequisites

For tests to run successfully, ensure:
1. All dependent modules are installed (`tw_menu`, `tw_branch`, `tw_partner`, etc.)
2. Test database is properly configured
3. Required master data exists (countries, states, etc.)
4. File storage system is configured (`tw_config_files`)

## Notes

- Tests use `TransactionCase` which automatically rolls back database changes after each test
- Some tests may be skipped if required master data is not available
- Mock data is created in `setUpClass` to minimize database calls
- Tests follow Odoo naming conventions (test_01_, test_02_, etc.)

## Adding New Tests

When adding new tests:
1. Follow the existing naming convention
2. Add appropriate docstrings
3. Use the `common.py` helpers where applicable
4. Tag tests appropriately
5. Ensure tests are isolated and don't depend on execution order
