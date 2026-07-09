# 1: imports of python lib
import hashlib
import hmac
import base64
from datetime import datetime

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class PaymentTransactionInherit(models.Model):
    _inherit = "payment.transaction"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_payload_api_payment_qris(self, setting_api_payment_config_obj, api_payment_config_obj, process_type):
        payload = super()._get_payload_api_payment_qris(setting_api_payment_config_obj, api_payment_config_obj, process_type)
        if api_payment_config_obj:
            if 'BCA' in api_payment_config_obj.api_type_value.upper() and api_payment_config_obj.is_api_payment:
                x_partner_id = setting_api_payment_config_obj.x_partner_id
                vals = {
                    'partnerServiceId': '   ' + x_partner_id,
                    'customerNo': self.transaction_keys,
                    'virtualAccountNo': self.va_no or '   ' + x_partner_id + self.transaction_keys,
                    'inquiryRequestId': self.transaction_id,
                    'paymentRequestId': self.transaction_id,
                    'additionalInfo': {}
                }
                if payload:
                    payload.update(vals)
                else:
                    payload = vals

        return payload
    
    def _generate_signature_headers(self, config_obj, str_to_sign):
        signature = super()._generate_signature_headers(config_obj, str_to_sign)
        if config_obj:
            if 'BCA' in config_obj.api_type_value.upper() and config_obj.is_api_payment:
                signature = hmac.new(str(config_obj.client_secret).encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha512).digest()
                signature = base64.b64encode(signature).decode('utf-8')

        return signature
    
    def _get_log_name_inquiry_api_payment_qris(self, api_payment_config_obj):
        log_name = super()._get_log_name_inquiry_api_payment_qris(api_payment_config_obj)
        if api_payment_config_obj:
            if 'BCA' in api_payment_config_obj.api_type_value.upper() and api_payment_config_obj.is_api_payment:
                log_name = 'Inquiry VA Payment BCA'

        return log_name
    
    def _process_inquiry_api_payment_va_response_content(self, response_content, api_payment_config_obj):
        values = {}
        response = super()._process_inquiry_api_payment_va_response_content(response_content, api_payment_config_obj)
        if response:
            values = response
        else:
            if api_payment_config_obj:
                if 'BCA' in api_payment_config_obj.api_type_value.upper() and api_payment_config_obj.is_api_payment:
                    if not response:
                        response = response_content

                    virtual_account_data = response.get('virtualAccountData')
                    paymentFlagStatus = virtual_account_data.get('paymentFlagStatus')
                    paymentFlagReason = virtual_account_data.get('paymentFlagReason')
                    partnerServiceId = virtual_account_data.get('partnerServiceId')
                    customerNo = virtual_account_data.get('customerNo')
                    virtualAccountNo = virtual_account_data.get('virtualAccountNo')
                    virtualAccountName = virtual_account_data.get('virtualAccountName')
                    inquiryRequestId = virtual_account_data.get('inquiryRequestId')
                    paymentRequestId = virtual_account_data.get('paymentRequestId')
                    channelCode = virtual_account_data.get('channelCode')
                    hashedSourceAccountNo = virtual_account_data.get('hashedSourceAccountNo')
                    sourceBankCode = virtual_account_data.get('sourceBankCode')
                    paidAmount = virtual_account_data.get('paidAmount')
                    cumulativePaymentAmount = virtual_account_data.get('cumulativePaymentAmount')
                    paidBills = virtual_account_data.get('paidBills')
                    totalAmount = virtual_account_data.get('totalAmount')
                    trxDateTime = virtual_account_data.get('transactionDate')
                    referenceNo = virtual_account_data.get('referenceNo')
                    flagAdvise = virtual_account_data.get('flagAdvise')
                    subCompany = virtual_account_data.get('subCompany')
                    billDetails = virtual_account_data.get('billDetails')
                    additionalInfo = virtual_account_data.get('additionalInfo')

                    values.update({'reference_number': referenceNo})
                    detail_info = f'partnerServiceId: {partnerServiceId}\n'
                    detail_info += f'customerNo: {customerNo}\n'
                    detail_info += f'virtualAccountNo: {virtualAccountNo}\n'
                    if virtualAccountName:
                        detail_info += f'virtualAccountName: {str(virtualAccountName)}\n'
                    if inquiryRequestId:
                        detail_info += f'inquiryRequestId: {str(inquiryRequestId)}\n'
                    detail_info += f'paymentRequestId: {paymentRequestId}\n'
                    if channelCode:
                        detail_info += f'channelCode: {str(channelCode)}\n'
                    if hashedSourceAccountNo:
                        detail_info += f'hashedSourceAccountNo: {str(hashedSourceAccountNo)}\n'
                    if sourceBankCode:
                        detail_info += f'sourceBankCode: {str(sourceBankCode)}\n'
                    detail_info += f'paidAmount: {str(paidAmount)}\n'
                    if referenceNo:
                        detail_info += f'referenceNo: {str(referenceNo)}\n'
                    if flagAdvise:
                        detail_info += f'flagAdvise: {str(flagAdvise)}\n'
                    if subCompany:
                        detail_info += f'subCompany: {str(subCompany)}\n'
                    if billDetails:
                        detail_info += f'billDetails: {str(billDetails)}\n'
                    if additionalInfo:
                        detail_info += f'additionalInfo: {str(additionalInfo)}\n'
                    values['detail_info'] = detail_info

                    # * check to make sure is already full paid or not
                    is_paid = False
                    if (paidAmount and totalAmount) or (paidAmount and self.amount):
                        if float(self.amount) == float(paidAmount.get('value')) and paymentFlagStatus == '00':
                            is_paid = True
                    if is_paid:
                        if trxDateTime:
                            trxDateTime = trxDateTime[:-6] + 'Z'
                        values.update({
                            'reason': 'Success',
                            'transaction_status': '1',
                            'transaction_date': datetime.strptime(trxDateTime, '%Y-%m-%dT%H:%M:%SZ'),
                            'state': 'paid'
                        })

                    if values.get('state') == 'declined':
                        values['state'] = 'cancel'
                    elif values.get('state') == 'invalid':
                        values['state'] = 'error'
                    elif values.get('state') == 'unpaid':
                        values['state'] = 'pending'
                    elif values.get('state') == 'paid':
                        values['state'] = 'done'
                    elif not values.get('state'):
                        values['state'] = 'error'

        return values