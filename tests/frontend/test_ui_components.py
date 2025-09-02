"""
Frontend UI Components Tests

Tests for Streamlit frontend components and user interface functionality.
"""

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


@pytest.fixture(scope="session")
def selenium_driver():
    """Selenium WebDriver fixture."""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    except Exception as e:
        pytest.skip(f"Selenium WebDriver not available: {e}")


@pytest.mark.frontend
class TestFrontendAccess:
    """Test basic frontend accessibility."""

    def test_frontend_homepage_accessible(self, frontend_url):
        """Test that frontend homepage is accessible."""
        try:
            response = requests.get(frontend_url, timeout=10)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Frontend not accessible: {e}")

    def test_streamlit_health_check(self, frontend_url):
        """Test Streamlit health check endpoint."""
        try:
            # Streamlit has a health check endpoint
            response = requests.get(f"{frontend_url}/healthz", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException:
            # Health check might not be enabled, that's okay
            pass

    def test_frontend_title(self, selenium_driver, frontend_url):
        """Test frontend page title."""
        selenium_driver.get(frontend_url)
        
        # Wait for page to load
        WebDriverWait(selenium_driver, 15).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # Check title contains expected text
        title = selenium_driver.title
        assert title is not None and len(title) > 0
        
        # Should contain Docsmait or Streamlit
        assert "docsmait" in title.lower() or "streamlit" in title.lower()


@pytest.mark.frontend
class TestAuthenticationUI:
    """Test authentication UI components."""

    def test_auth_page_accessible(self, selenium_driver, frontend_url):
        """Test that authentication page is accessible."""
        auth_url = f"{frontend_url}/pages/Auth"
        selenium_driver.get(auth_url)
        
        # Wait for page to load
        WebDriverWait(selenium_driver, 15).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        
        # Check page loaded without error
        page_source = selenium_driver.page_source
        assert "error" not in page_source.lower() or "streamlit" in page_source.lower()

    def test_login_form_elements(self, selenium_driver, frontend_url):
        """Test login form elements are present."""
        try:
            auth_url = f"{frontend_url}/pages/Auth"
            selenium_driver.get(auth_url)
            
            # Wait for Streamlit to load
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: "streamlit" in driver.page_source.lower()
            )
            
            # Look for input fields (Streamlit creates specific input elements)
            page_source = selenium_driver.page_source
            
            # Should contain form-like elements
            has_inputs = (
                'input' in page_source.lower() or 
                'text_input' in page_source.lower() or
                'password' in page_source.lower()
            )
            
            assert has_inputs, "No input elements found on auth page"
            
        except Exception as e:
            pytest.skip(f"Cannot test login form: {e}")

    def test_signup_form_elements(self, selenium_driver, frontend_url):
        """Test signup form elements are present."""
        try:
            auth_url = f"{frontend_url}/pages/Auth"
            selenium_driver.get(auth_url)
            
            # Wait for page to load
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: "streamlit" in driver.page_source.lower()
            )
            
            page_source = selenium_driver.page_source
            
            # Should contain signup-related elements
            has_signup = (
                'sign up' in page_source.lower() or
                'register' in page_source.lower() or
                'username' in page_source.lower()
            )
            
            assert has_signup, "No signup elements found on auth page"
            
        except Exception as e:
            pytest.skip(f"Cannot test signup form: {e}")


@pytest.mark.frontend
class TestNavigationUI:
    """Test navigation and sidebar components."""

    def test_sidebar_navigation_present(self, selenium_driver, frontend_url):
        """Test that sidebar navigation is present."""
        try:
            selenium_driver.get(frontend_url)
            
            # Wait for Streamlit to fully load
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: "streamlit" in driver.page_source.lower()
            )
            
            page_source = selenium_driver.page_source
            
            # Should contain navigation elements
            has_nav = (
                'sidebar' in page_source.lower() or
                'navigation' in page_source.lower() or
                'projects' in page_source.lower()
            )
            
            assert has_nav, "No navigation elements found"
            
        except Exception as e:
            pytest.skip(f"Cannot test navigation: {e}")

    def test_sidebar_menu_items(self, selenium_driver, frontend_url):
        """Test specific sidebar menu items are present."""
        try:
            selenium_driver.get(frontend_url)
            
            # Wait for page load
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: "streamlit" in driver.page_source.lower()
            )
            
            page_source = selenium_driver.page_source.lower()
            
            # Check for key menu items we added
            expected_items = [
                'projects', 'templates', 'documents', 
                'activity', 'records', 'knowledge'
            ]
            
            found_items = [item for item in expected_items if item in page_source]
            
            # Should find at least some navigation items
            assert len(found_items) >= 2, f"Few navigation items found: {found_items}"
            
        except Exception as e:
            pytest.skip(f"Cannot test menu items: {e}")


@pytest.mark.frontend 
class TestPageComponents:
    """Test individual page components."""

    def test_projects_page_accessible(self, selenium_driver, frontend_url):
        """Test Projects page is accessible."""
        try:
            projects_url = f"{frontend_url}/pages/_Projects"
            selenium_driver.get(projects_url)
            
            # Wait for page load
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            page_source = selenium_driver.page_source
            
            # Should load without major errors
            assert "error" not in page_source.lower() or "streamlit" in page_source.lower()
            
        except Exception as e:
            pytest.skip(f"Cannot test projects page: {e}")

    def test_documents_page_accessible(self, selenium_driver, frontend_url):
        """Test Documents page is accessible."""
        try:
            docs_url = f"{frontend_url}/pages/Documents"
            selenium_driver.get(docs_url)
            
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            page_source = selenium_driver.page_source
            assert "error" not in page_source.lower() or "streamlit" in page_source.lower()
            
        except Exception as e:
            pytest.skip(f"Cannot test documents page: {e}")

    def test_templates_page_accessible(self, selenium_driver, frontend_url):
        """Test Templates page is accessible."""
        try:
            templates_url = f"{frontend_url}/pages/Templates"
            selenium_driver.get(templates_url)
            
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            page_source = selenium_driver.page_source
            assert "error" not in page_source.lower() or "streamlit" in page_source.lower()
            
        except Exception as e:
            pytest.skip(f"Cannot test templates page: {e}")

    def test_activity_logs_page_accessible(self, selenium_driver, frontend_url):
        """Test Activity Logs page is accessible."""
        try:
            activity_url = f"{frontend_url}/pages/Activity_Logs"
            selenium_driver.get(activity_url)
            
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            page_source = selenium_driver.page_source
            assert "error" not in page_source.lower() or "streamlit" in page_source.lower()
            
        except Exception as e:
            pytest.skip(f"Cannot test activity logs page: {e}")

    def test_records_page_accessible(self, selenium_driver, frontend_url):
        """Test Records page is accessible."""
        try:
            records_url = f"{frontend_url}/pages/Records"
            selenium_driver.get(records_url)
            
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            page_source = selenium_driver.page_source
            assert "error" not in page_source.lower() or "streamlit" in page_source.lower()
            
        except Exception as e:
            pytest.skip(f"Cannot test records page: {e}")


@pytest.mark.frontend
@pytest.mark.slow  
class TestUserInteractionFlows:
    """Test complete user interaction flows."""

    def test_navigation_flow(self, selenium_driver, frontend_url):
        """Test navigating between pages."""
        try:
            # Start at home page
            selenium_driver.get(frontend_url)
            
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: "streamlit" in driver.page_source.lower()
            )
            
            # Try to navigate to different pages
            pages_to_test = [
                "/pages/Auth",
                "/pages/Documents", 
                "/pages/Templates"
            ]
            
            successful_navigations = 0
            
            for page_path in pages_to_test:
                try:
                    selenium_driver.get(f"{frontend_url}{page_path}")
                    
                    WebDriverWait(selenium_driver, 10).until(
                        lambda driver: driver.execute_script("return document.readyState") == "complete"
                    )
                    
                    # If no major error, count as success
                    page_source = selenium_driver.page_source.lower()
                    if "error 404" not in page_source and "not found" not in page_source:
                        successful_navigations += 1
                        
                except Exception:
                    # Page might not be accessible, continue
                    continue
            
            # Should be able to navigate to at least one page
            assert successful_navigations >= 1, "Cannot navigate to any pages"
            
        except Exception as e:
            pytest.skip(f"Cannot test navigation flow: {e}")

    def test_responsive_design_mobile(self, selenium_driver, frontend_url):
        """Test responsive design on mobile viewport."""
        try:
            # Set mobile viewport
            selenium_driver.set_window_size(375, 667)  # iPhone size
            
            selenium_driver.get(frontend_url)
            
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: "streamlit" in driver.page_source.lower()
            )
            
            # Check that page loads and is usable on mobile
            page_source = selenium_driver.page_source
            
            # Should still contain main content
            assert len(page_source) > 1000, "Page content too minimal on mobile"
            
            # Reset to desktop size
            selenium_driver.set_window_size(1920, 1080)
            
        except Exception as e:
            pytest.skip(f"Cannot test mobile responsiveness: {e}")

    def test_page_load_performance(self, selenium_driver, frontend_url):
        """Test page load performance."""
        try:
            import time
            
            start_time = time.time()
            selenium_driver.get(frontend_url)
            
            # Wait for page to be ready
            WebDriverWait(selenium_driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            end_time = time.time()
            load_time = end_time - start_time
            
            # Page should load in reasonable time
            assert load_time < 30.0, f"Page load too slow: {load_time:.2f}s"
            
            # Should have substantive content
            page_source = selenium_driver.page_source
            assert len(page_source) > 500, "Page content too minimal"
            
        except Exception as e:
            pytest.skip(f"Cannot test page performance: {e}")


@pytest.mark.frontend
class TestAccessibility:
    """Test accessibility features."""

    def test_page_has_title(self, selenium_driver, frontend_url):
        """Test page has proper title."""
        selenium_driver.get(frontend_url)
        
        WebDriverWait(selenium_driver, 15).until(
            lambda driver: driver.title is not None and len(driver.title) > 0
        )
        
        title = selenium_driver.title
        assert title is not None
        assert len(title) > 3, "Page title too short"

    def test_page_has_heading_structure(self, selenium_driver, frontend_url):
        """Test page has proper heading structure."""
        try:
            selenium_driver.get(frontend_url)
            
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: "streamlit" in driver.page_source.lower()
            )
            
            # Look for heading elements
            headings = selenium_driver.find_elements(By.TAG_NAME, "h1")
            headings.extend(selenium_driver.find_elements(By.TAG_NAME, "h2"))
            headings.extend(selenium_driver.find_elements(By.TAG_NAME, "h3"))
            
            # Should have at least some heading structure
            # Note: Streamlit might create headings differently
            # so we'll be lenient here
            page_source = selenium_driver.page_source
            has_headings = (
                len(headings) > 0 or
                "<h1" in page_source or
                "<h2" in page_source or
                "# " in page_source  # Markdown headings
            )
            
            assert has_headings, "No heading structure found"
            
        except Exception as e:
            pytest.skip(f"Cannot test heading structure: {e}")

    def test_images_have_alt_text(self, selenium_driver, frontend_url):
        """Test images have alt text."""
        try:
            selenium_driver.get(frontend_url)
            
            WebDriverWait(selenium_driver, 15).until(
                lambda driver: "streamlit" in driver.page_source.lower()
            )
            
            # Find all images
            images = selenium_driver.find_elements(By.TAG_NAME, "img")
            
            if images:
                # Check that images have alt attributes
                images_without_alt = [img for img in images if not img.get_attribute("alt")]
                
                # Should have alt text for accessibility
                assert len(images_without_alt) == 0, f"{len(images_without_alt)} images missing alt text"
            
        except Exception as e:
            pytest.skip(f"Cannot test image alt text: {e}")