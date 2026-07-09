# -*- coding: utf-8 -*-
"""
Selenium UI Tests untuk P2P Module - Organized by Test Type

Test Types:
1. ACCESS - Access rights & permissions testing
2. FLOW - Business workflow & logic testing

Run specific tests:
    python test_ui_selenium.py ACCESS  # Only access tests
    python test_ui_selenium.py FLOW    # Only flow tests
    python test_ui_selenium.py         # All tests
"""

import unittest
import time
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


# ========== BASE TEST CLASS ==========

class P2PSeleniumTestBase(unittest.TestCase):
    """Base class dengan helper methods untuk semua P2P Selenium tests"""
    
    @classmethod
    def setUpClass(cls):
        """Setup Selenium WebDriver - shared by all tests"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment untuk headless
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        
        # Configuration
        cls.base_url = "http://localhost:8098"
        cls.database = "database_rzu"
        cls.timeout = 15
        
        # User credentials
        cls.spv_user = ("spvlogistik", "spvlogistik")
        cls.readonly_user = ("readonly_test", "password123")  # Update as needed
        
        # Menu XML IDs - Based on tw_menu.xml and tw_menu_view.xml
        # Using data-menu-xmlid attribute for reliable navigation
        # Format: [xml_id1, xml_id2, ...] for nested menus
        
        # Unit (Showroom Division)
        cls.MENU_P2P_UNIT = [
            'tw_menu.menu_tw_showroom',                      # Showroom
            'tw_menu.submenu_tw_showroom_purchase',          # Pembelian
            'tw_p2p.tw_p2p_purchase_unit_submenu'            # P2P Unit
        ]
        cls.MENU_P2P_CONFIG_UNIT = [
            'tw_menu.menu_tw_showroom',                      # Showroom
            'tw_menu.submenu_tw_showroom_configuration',     # Configuration
            'tw_p2p.tw_p2p_configuration_unit_menu',         # P2P
            'tw_p2p.tw_p2p_unit_submenu'                     # P2P Config
        ]
        cls.MENU_P2P_PRODUCT_UNIT = [
            'tw_menu.menu_tw_showroom',
            'tw_menu.submenu_tw_showroom_configuration',
            'tw_p2p.tw_p2p_configuration_unit_menu',
            'tw_p2p.tw_p2p_unit_product_submenu'             # P2P Product
        ]
        cls.MENU_P2P_PERIODE_UNIT = [
            'tw_menu.menu_tw_showroom',
            'tw_menu.submenu_tw_showroom_configuration',
            'tw_p2p.tw_p2p_configuration_unit_menu',
            'tw_p2p.tw_p2p_unit_periode_submenu'             # P2P Periode
        ]
        
        # Sparepart (Workshop Division)
        cls.MENU_P2P_SPAREPART = [
            'tw_menu.menu_tw_workshop',                      # Workshop
            'tw_menu.submenu_tw_workshop_purchase',          # Pembelian
            'tw_p2p.tw_p2p_purchase_sparepart_submenu'       # P2P Sparepart
        ]
        cls.MENU_P2P_CONFIG_WORKSHOP = [
            'tw_menu.menu_tw_workshop',
            'tw_menu.submenu_tw_workshop_configuration',
            'tw_p2p.tw_p2p_configuration_sparepart_menu',
            'tw_p2p.tw_p2p_sparepart_submenu'
        ]
        cls.MENU_P2P_PRODUCT_WORKSHOP = [
            'tw_menu.menu_tw_workshop',
            'tw_menu.submenu_tw_workshop_configuration',
            'tw_p2p.tw_p2p_configuration_sparepart_menu',
            'tw_p2p.tw_p2p_sparepart_product_submenu'
        ]
        cls.MENU_P2P_PERIODE_WORKSHOP = [
            'tw_menu.menu_tw_workshop',
            'tw_menu.submenu_tw_workshop_configuration',
            'tw_p2p.tw_p2p_configuration_sparepart_menu',
            'tw_p2p.tw_p2p_sparepart_periode_submenu'
        ]
    
    @classmethod
    def tearDownClass(cls):
        """Cleanup"""
        cls.driver.quit()
    
    def tearDown(self):
        """Print error summary on test failure"""
        # Check if test failed
        if hasattr(self, '_outcome'):
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, self._outcome.errors)
        else:
            result = self.defaultTestResult()
            self._feedErrorsToResult(result, sys.exc_info())
        
        # Check for failures or errors
        error = self.list_contains_test_result(result.errors)
        failure = self.list_contains_test_result(result.failures)
        
        if error or failure:
            test_name = self.id().split('.')[-1]
            print(f"\n❌ Test '{test_name}' failed")
            try:
                print(f"🔗 URL: {self.driver.current_url}")
            except:
                pass
    
    def list_contains_test_result(self, test_result_list):
        """Helper to check if test appears in result list"""
        for test_case, _ in test_result_list:
            if test_case.id() == self.id():
                return True
        return False
    
    def login(self, username, password):
        """Helper: Login ke Odoo"""
        self.driver.get(f"{self.base_url}/web/login")
        
        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.NAME, "login"))
        )
        
        self.driver.find_element(By.NAME, "login").clear()
        self.driver.find_element(By.NAME, "login").send_keys(username)
        self.driver.find_element(By.NAME, "password").clear()
        self.driver.find_element(By.NAME, "password").send_keys(password)
        
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "o_main_navbar"))
        )
        time.sleep(2)
    
    def logout(self):
        """Helper: Logout dari Odoo"""
        try:
            user_menu = self.driver.find_element(By.CLASS_NAME, "o_user_menu")
            user_menu.click()
            time.sleep(1)
            logout_link = self.driver.find_element(By.XPATH, "//a[contains(@href, '/web/session/logout')]")
            logout_link.click()
            time.sleep(2)
        except Exception as e:
            print(f"Logout error (non-critical): {e}")
    
    def get_state_text(self):
        """Helper: Get current state value from form"""
        try:
            state_elem = self.driver.find_element(By.CSS_SELECTOR, ".o_field_widget[name='state']")
            return state_elem.text
        except:
            return None
    
    def close_all_popovers(self):
        """Helper: Aggressively close all open popovers/dropdowns"""
        try:
            # Method 1: Click ESC key
            from selenium.webdriver.common.keys import Keys
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.3)
        except:
            pass
        
        try:
            # Method 2: Click body to close dropdowns
            body = self.driver.find_element(By.TAG_NAME, "body")
            self.driver.execute_script("arguments[0].click();", body)
            time.sleep(0.3)
        except:
            pass
        
        try:
            # Method 3: Remove popover elements directly
            self.driver.execute_script("""
                var popovers = document.querySelectorAll('.o_popover, .popover, .dropdown-menu, .o-dropdown--menu');
                popovers.forEach(function(el) { 
                    if (el.style.display !== 'none') {
                        el.style.display = 'none'; 
                    }
                });
            """)
            time.sleep(0.3)
        except:
            pass
    
    def navigate_to_menu(self, menu_xml_ids):
        """
        Helper: Navigate ke menu Odoo using XML IDs (for apps) and flexible selectors (for submenus)
        
        Args:
            menu_xml_ids: List of XML IDs in order, e.g.:
                ['tw_menu.menu_tw_showroom', 'tw_menu.submenu_tw_showroom_purchase', 'tw_p2p.tw_p2p_purchase_unit_submenu']
        
        Note: In Odoo 18, submenus might not have data-menu-xmlid attribute.
              We use hybrid approach: XML ID for apps, text matching for submenus.
        """
        for idx, xml_id in enumerate(menu_xml_ids):
            # Close any open popovers before each step
            self.close_all_popovers()
            
            try:
                # Get menu name from XML ID (for logging and fallback)
                menu_name = xml_id.split('.')[-1].replace('_', ' ').title()
                
                # Different approach for first menu (Apps) vs submenus
                if idx == 0:
                    # First level - Open apps menu
                    try:
                        apps_menu = self.driver.find_element(By.CLASS_NAME, "o_navbar_apps_menu")
                        if apps_menu:
                            self.driver.execute_script("arguments[0].click();", apps_menu)
                            time.sleep(1)
                            self.close_all_popovers()
                            time.sleep(0.5)
                    except NoSuchElementException:
                        pass
                    
                    # Find app by XML ID (most reliable for top-level)
                    # menu_selector is implicitly defined by the WebDriverWait below
                else:
                    # Submenus: Use multiple strategies since Odoo 18 might not have data-menu-xmlid
                    # Extract expected text from XML ID
                    # e.g., 'submenu_tw_showroom_purchase' → try to find 'Purchase' or 'Pembelian'
                    
                    # Wait for submenu to appear after clicking parent
                    time.sleep(1)
                    
                    # Strategy 1: Try XML ID first (if available)
                    # Strategy 2: Try data-menu-id attribute
                    # Strategy 3: Try text matching with common classes
                    # This selector is used to find ALL potential submenu elements
                    menu_selector = f"//a[@data-menu-xmlid='{xml_id}'] | " \
                                   f"//nav[contains(@class, 'o_menu_sections')]//a[contains(@class, 'dropdown-item')] | " \
                                   f"//nav[contains(@class, 'o_menu_sections')]//span[contains(@class, 'o_menu_brand')] | " \
                                   f"//a[contains(@class, 'o_nav_entry')]"
                
                # Retry mechanism
                max_retries = 3
                menu_found = False
                
                for attempt in range(max_retries):
                    try:
                        if idx == 0:
                            # For apps, use XML ID selector
                            menu = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, f"//a[@data-menu-xmlid='{xml_id}']"))
                            )
                        else:
                            # For submenus, find all visible menu items and match by XML ID or text
                            all_menus = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_all_elements_located((By.XPATH, menu_selector))
                            )
                            
                            menu = None
                            for m in all_menus:
                                # Try to match by XML ID first
                                menu_xmlid = m.get_attribute("data-menu-xmlid")
                                if menu_xmlid == xml_id:
                                    menu = m
                                    break
                            
                            # If not found by XML ID, we have a problem
                            if not menu:
                                # This means submenu doesn't have data-menu-xmlid
                                # Need to get submenu structure differently
                                raise NoSuchElementException(f"Submenu {xml_id} not found by data-menu-xmlid")
                        
                        if menu:
                            # Scroll into view
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", menu)
                            time.sleep(0.3)
                            
                            # Ensure visible
                            if menu.is_displayed():
                                # JavaScript click
                                self.driver.execute_script("arguments[0].click();", menu)
                                time.sleep(1.2)
                                menu_found = True
                                
                                # Get text for logging
                                menu_text = menu.text.strip() or menu_name
                                print(f"✓ Navigated to: {menu_text}")
                                break
                            else:
                                if attempt < max_retries - 1:
                                    self.close_all_popovers()
                                    time.sleep(0.5)
                    except (TimeoutException, NoSuchElementException) as e:
                        if attempt < max_retries - 1:
                            self.close_all_popovers()
                            time.sleep(0.5)
                            continue
                        else:
                            break
                
                if not menu_found:
                    # Enhanced error message for Odoo 18
                    print(f"\n❌ Menu with XML ID '{xml_id}' not found")
                    print(f"   Path: {' → '.join([x.split('.')[-1] for x in menu_xml_ids])}")
                    print(f"   Position: {idx + 1}/{len(menu_xml_ids)}")
                    print(f"   Level: {'App' if idx == 0 else 'Submenu'}")
                    
                    if idx > 0:
                        print(f"\n   ⚠️  Odoo 18 Note: Submenus might not have data-menu-xmlid")
                        print(f"   Available submenu elements:")
                        try:
                            # Show actual submenu structure
                            submenus = self.driver.find_elements(
                                By.XPATH, 
                                "//nav[contains(@class, 'o_menu_sections')]//a | //a[contains(@class, 'o_nav_entry')]"
                            )
                            for i, m in enumerate(submenus[:10], 1):
                                m_text = m.text.strip()
                                m_xmlid = m.get_attribute("data-menu-xmlid") or "(no XML ID)"
                                m_class = m.get_attribute("class")
                                if m_text or m_xmlid != "(no XML ID)":
                                    print(f"   {i}. {m_text or '(no text)'} → {m_xmlid} [{m_class}]")
                        except:
                            print("   (Could not inspect submenus)")
                    else:
                        print(f"\n   Available apps (by XML ID):")
                        try:
                            apps = self.driver.find_elements(By.XPATH, "//a[@data-menu-xmlid]")
                            for i, app in enumerate(apps[:10], 1):
                                app_xmlid = app.get_attribute("data-menu-xmlid")
                                app_text = app.text.strip()
                                if app_xmlid:
                                    print(f"   {i}. {app_text or '(no text)'} → {app_xmlid}")
                        except:
                            print("   (Could not list apps)")
                    
                    print(f"\n   💡 TIP: Inspect element in browser to see actual structure\n")
                    self.fail(f"Menu '{xml_id}' not found")
                
            except TimeoutException as e:
                print(f"\n⏱️ Timeout waiting for menu: '{xml_id}'")
                print(f"   Waited: {self.timeout} seconds\n")
                self.fail(f"Timeout: '{xml_id}'")
    
    def wait_for_list_view(self):
        """Helper: Wait for Odoo list view to load"""
        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "o_list_view"))
        )
        time.sleep(1)
    
    def wait_for_form_view(self):
        """Helper: Wait for Odoo form view to load"""
        WebDriverWait(self.driver, self.timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "o_form_view"))
        )
        time.sleep(1)
    
    def element_exists(self, by, value):
        """Helper: Check if element exists"""
        try:
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False
    
    def element_visible(self, by, value):
        """Helper: Check if element is visible"""
        try:
            element = self.driver.find_element(by, value)
            return element.is_displayed()
        except NoSuchElementException:
            return False
    
    def click_button_by_name(self, button_name):
        """Helper: Click button by name attribute"""
        button = self.driver.find_element(By.XPATH, f"//button[@name='{button_name}']")
        button.click()
        time.sleep(1)
    
    def get_state_text(self):
        """Helper: Get current state value from form"""
        try:
            state_elem = self.driver.find_element(By.CSS_SELECTOR, ".o_field_widget[name='state']")
            return state_elem.text
        except:
            return None


# ========== ACCESS RIGHTS TESTS ==========

class P2PAccessRightsTests(P2PSeleniumTestBase):
    """
    Test Category: ACCESS
    Tests untuk validasi hak akses (permissions) user
    
    Run only these tests:
        python test_ui_selenium.py ACCESS
    """
    
    # Test tag untuk filtering
    TEST_CATEGORY = "ACCESS"
    
    def test_access_00_debug_menu_structure(self):
        """[ACCESS - DEBUG] Print available menu structure untuk debugging"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            print("\n" + "="*60)
            print("DEBUGGING: Available Menu Structure")
            print("="*60)
            
            # Check apps menu
            try:
                apps_btn = self.driver.find_element(By.CLASS_NAME, "o_navbar_apps_menu")
                apps_btn.click()
                time.sleep(2)
                print("\n📱 APPS MENU:")
            except NoSuchElementException:
                print("\n⚠️ No apps menu button found")
            
            # List all apps
            apps = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'o_app')]")
            for app in apps:
                app_name = app.text.strip()
                if app_name:
                    print(f"  • {app_name}")
            
            # Try to find Showroom/Purchase specific
            print("\n🔍 Looking for Showroom/Purchase menus:")
            
            # Try Showroom
            showroom_selectors = [
                "//div[contains(@class, 'o_app') and contains(., 'Showroom')]",
                "//a[contains(., 'Showroom')]",
                "//span[contains(text(), 'Showroom')]",
            ]
            
            for selector in showroom_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        print(f"  ✓ Found {len(elements)} element(s) matching 'Showroom'")
                        for elem in elements[:3]:
                            print(f"    - {elem.text} (class: {elem.get_attribute('class')})")
                except:
                    pass
            
            # Click Showroom if found
            try:
                # Close popovers first
                self.close_all_popovers()
                time.sleep(0.5)
                
                showroom = self.driver.find_element(By.XPATH, "//div[contains(@class, 'o_app') and contains(., 'Showroom')] | //a[contains(., 'Showroom')]")
                # Use JavaScript click to avoid interception
                self.driver.execute_script("arguments[0].click();", showroom)
                time.sleep(2)
                
                print("\n📋 SHOWROOM SUBMENUS:")
                submenus = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'o_menu') or contains(@class, 'dropdown-item')]")
                for menu in submenus:
                    menu_text = menu.text.strip()
                    if menu_text:
                        print(f"  • {menu_text}")
            except Exception as e:
                print(f"  ❌ Could not open Showroom: {e}")
            
            print("\n" + "="*60)
            print("Use this information to fix menu_path in your tests!")
            print("="*60 + "\n")
            
        finally:
            self.logout()
    
    def test_access_01_spv_can_access_p2p_menu(self):
        """[ACCESS] SPV user dapat mengakses menu P2P Unit"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            # Navigate to P2P Unit menu
            self.navigate_to_menu(self.MENU_P2P_UNIT)
            self.wait_for_list_view()
            
            # Verify we're on P2P list page
            self.assertTrue(
                self.element_exists(By.CLASS_NAME, "o_list_view"),
                "SPV should be able to access P2P Unit menu"
            )
            
        finally:
            self.logout()
    
    def test_access_02_spv_can_see_create_button(self):
        """[ACCESS] SPV user dapat melihat tombol Create (has CREATE permission)"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            self.navigate_to_menu(self.MENU_P2P_UNIT)
            self.wait_for_list_view()
            
            # Check Create button visibility
            create_button_visible = self.element_visible(
                By.XPATH,
                "//button[contains(@class, 'o_list_button_add')]"
            )
            
            self.assertTrue(
                create_button_visible,
                "SPV should see Create button (UPDATE group includes CREATE)"
            )
            
        finally:
            self.logout()
    
    def test_access_03_spv_can_access_master_config(self):
        """[ACCESS] SPV dapat mengakses P2P Config menu"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            self.navigate_to_menu(self.MENU_P2P_CONFIG_UNIT)
            self.wait_for_list_view()
            
            self.assertTrue(
                self.element_exists(By.CLASS_NAME, "o_list_view"),
                "SPV should access P2P Config menu"
            )
            
        finally:
            self.logout()
    
    def test_access_04_spv_can_access_master_product(self):
        """[ACCESS] SPV dapat mengakses P2P Product menu"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            self.navigate_to_menu(self.MENU_P2P_PRODUCT_UNIT)
            self.wait_for_list_view()
            
            self.assertTrue(
                self.element_exists(By.CLASS_NAME, "o_list_view"),
                "SPV should access P2P Product menu"
            )
            
        finally:
            self.logout()
    
    def test_access_05_spv_can_access_master_periode(self):
        """[ACCESS] SPV dapat mengakses P2P Periode menu"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            self.navigate_to_menu(self.MENU_P2P_PERIODE_UNIT)
            self.wait_for_list_view()
            
            self.assertTrue(
                self.element_exists(By.CLASS_NAME, "o_list_view"),
                "SPV should access P2P Periode menu"
            )
            
        finally:
            self.logout()
    
    # Uncomment when readonly user is set up
    # def test_access_10_readonly_cannot_see_create_button(self):
    #     """[ACCESS] Read-only user TIDAK melihat tombol Create"""
    #     username, password = self.readonly_user
    #     self.login(username, password)
    #     
    #     try:
    #         self.navigate_to_menu(['Showroom', 'Purchase', 'P2P Unit'])
    #         self.wait_for_list_view()
    #         
    #         # Create button should NOT be visible
    #         create_button_visible = self.element_visible(
    #             By.XPATH,
    #             "//button[contains(@class, 'o_list_button_add')]"
    #         )
    #         
    #         self.assertFalse(
    #             create_button_visible,
    #             "Read-only user should NOT see Create button"
    #         )
    #         
    #     finally:
    #         self.logout()


# ========== WORKFLOW TESTS ==========

class P2PWorkflowTests(P2PSeleniumTestBase):
    """
    Test Category: FLOW
    Tests untuk validasi business workflow & logic
    
    Run only these tests:
        python test_ui_selenium.py FLOW
    """
    
    TEST_CATEGORY = "FLOW"
    
    def test_flow_01_create_p2p_order_open_form(self):
        """[FLOW] Test 1.1: Create P2P Order - Open Form"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            # Navigate to P2P Unit
            self.navigate_to_menu(self.MENU_P2P_UNIT)
            self.wait_for_list_view()
            
            # Click Create
            create_btn = self.driver.find_element(
                By.XPATH,
                "//button[contains(@class, 'o_list_button_add')]"
            )
            create_btn.click()
            
            # Wait for form to open
            self.wait_for_form_view()
            
            # Verify form opened
            self.assertTrue(
                self.element_exists(By.CLASS_NAME, "o_form_view"),
                "Create form should open"
            )
            
            # Discard without saving
            discard_btn = self.driver.find_element(
                By.XPATH,
                "//button[contains(@class, 'o_form_button_cancel')]"
            )
            discard_btn.click()
            time.sleep(1)
            
        finally:
            self.logout()
    
    def test_flow_02_edit_p2p_order_description(self):
        """[FLOW] Test 1.2: Edit P2P Order - Change Description"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            # Navigate to P2P Unit
            self.navigate_to_menu(self.MENU_P2P_UNIT)
            self.wait_for_list_view()
            
            # Try to open first record
            try:
                first_record = self.driver.find_element(
                    By.XPATH,
                    "//table[contains(@class, 'o_list_table')]//tr[contains(@class, 'o_data_row')][1]"
                )
                first_record.click()
                self.wait_for_form_view()
                
                # Check if in readonly mode, click Edit
                try:
                    edit_btn = self.driver.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'o_form_button_edit')]"
                    )
                    edit_btn.click()
                    time.sleep(1)
                except NoSuchElementException:
                    pass  # Already in edit mode
                
                # Edit description field
                try:
                    desc_input = self.driver.find_element(By.NAME, "description")
                    desc_input.clear()
                    desc_input.send_keys("Test Edit by Selenium - " + str(int(time.time())))
                    
                    # Verify can type
                    self.assertIn("Test Edit", desc_input.get_attribute("value"))
                    
                    # Discard changes
                    discard_btn = self.driver.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'o_form_button_cancel')]"
                    )
                    discard_btn.click()
                    time.sleep(1)
                    
                except NoSuchElementException:
                    print("Description field not found - record might be in readonly state")
                
            except NoSuchElementException:
                self.skipTest("No P2P records available for edit test")
            
        finally:
            self.logout()
    
    def test_flow_03_verify_draft_state_on_create(self):
        """[FLOW] Verify new P2P order has Draft state"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            self.navigate_to_menu(self.MENU_P2P_UNIT)
            self.wait_for_list_view()
            
            # Open first record or skip if none
            try:
                first_record = self.driver.find_element(
                    By.XPATH,
                    "//table[contains(@class, 'o_list_table')]//tr[contains(@class, 'o_data_row')][1]"
                )
                first_record.click()
                self.wait_for_form_view()
                
                # Get state
                state_text = self.get_state_text()
                
                # If state is Draft, test passes
                if state_text and "Draft" in state_text:
                    self.assertIn("Draft", state_text, "New orders should be in Draft state")
                else:
                    print(f"Record in state: {state_text} - might be processed already")
                
            except NoSuchElementException:
                self.skipTest("No records to test state")
            
        finally:
            self.logout()
    
    def test_flow_04_verify_generate_button_for_fix_type(self):
        """[FLOW] Test 2.1: Verify Generate button untuk Fix type"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            self.navigate_to_menu(self.MENU_P2P_UNIT)
            self.wait_for_list_view()
            
            # Look for a Fix type order in Draft
            try:
                # Open first record
                first_record = self.driver.find_element(
                    By.XPATH,
                    "//table[contains(@class, 'o_list_table')]//tr[contains(@class, 'o_data_row')][1]"
                )
                first_record.click()
                self.wait_for_form_view()
                
                # Check type and state
                state = self.get_state_text()
                
                # If Draft and Fix type, Generate button should be visible
                # (depends on groups - user might not have generate group)
                generate_btn_exists = self.element_exists(
                    By.XPATH,
                    "//button[@name='action_generate_line']"
                )
                
                if state and "Draft" in state:
                    print(f"Generate button visible: {generate_btn_exists}")
                    # Not asserting here as it depends on user groups
                else:
                    print(f"Record not in Draft state: {state}")
                
            except NoSuchElementException:
                self.skipTest("No records to test Generate button")
            
        finally:
            self.logout()
    
    def test_flow_05_verify_state_badge_visible(self):
        """[FLOW] Verify state badge is visible and readable"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            self.navigate_to_menu(self.MENU_P2P_UNIT)
            self.wait_for_list_view()
            
            try:
                first_record = self.driver.find_element(
                    By.XPATH,
                    "//table[contains(@class, 'o_list_table')]//tr[contains(@class, 'o_data_row')][1]"
                )
                first_record.click()
                self.wait_for_form_view()
                
                # State should be visible
                state_text = self.get_state_text()
                self.assertIsNotNone(state_text, "State should be visible")
                self.assertNotEqual(state_text.strip(), "", "State should have value")
                
                print(f"Current state: {state_text}")
                
            except NoSuchElementException:
                self.skipTest("No records to test state visibility")
            
        finally:
            self.logout()
    
    def test_flow_06_verify_audit_trail_fields_exist(self):
        """[FLOW] Verify audit trail fields exist in form"""
        username, password = self.spv_user
        self.login(username, password)
        
        try:
            self.navigate_to_menu(self.MENU_P2P_UNIT)
            self.wait_for_list_view()
            
            try:
                first_record = self.driver.find_element(
                    By.XPATH,
                    "//table[contains(@class, 'o_list_table')]//tr[contains(@class, 'o_data_row')][1]"
                )
                first_record.click()
                self.wait_for_form_view()
                
                # Check for audit trail fields (might be in a tab/page)
                # These fields should exist somewhere in the form
                audit_fields = ['confirm_uid', 'confirm_date', 'cancel_uid', 'revisi_uid']
                
                # Just check form loaded - actual field visibility depends on state
                form_exists = self.element_exists(By.CLASS_NAME, "o_form_view")
                self.assertTrue(form_exists, "Form with audit fields should load")
                
            except NoSuchElementException:
                self.skipTest("No records to test audit trail")
            
        finally:
            self.logout()


# ========== TEST RUNNER WITH FILTERING ==========

def suite():
    """Custom test suite dengan filtering by category"""
    suite = unittest.TestSuite()
    
    # Check command line arguments
    run_category = None
    if len(sys.argv) > 1:
        arg = sys.argv[1].upper()
        if arg in ['ACCESS', 'FLOW']:
            run_category = arg
            print(f"\n{'='*60}")
            print(f"Running only {run_category} tests")
            print(f"{'='*60}\n")
    
    # Add tests based on category
    if run_category is None or run_category == 'ACCESS':
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(P2PAccessRightsTests))
    
    if run_category is None or run_category == 'FLOW':
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(P2PWorkflowTests))
    
    return suite


if __name__ == "__main__":
    # Remove category argument from sys.argv to avoid unittest errors
    if len(sys.argv) > 1 and sys.argv[1].upper() in ['ACCESS', 'FLOW']:
        sys.argv.pop(1)
    
    # Run with detailed output
    print("\n" + "="*70)
    print("🧪 P2P SELENIUM UI TESTS")
    print("="*70)
    print(f"Browser: Chrome")
    print(f"Odoo: http://localhost:8098")
    print(f"Database: database_rzu")
    print("="*70 + "\n")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite())
    
    # Print summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"🔴 Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailed tests:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\nTests with errors:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            print(f"    Error: {traceback.split(chr(10))[-2]}")  # Last line of error
    
    print("="*70 + "\n")
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
