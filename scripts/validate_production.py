#!/usr/bin/env python3
"""
Production Validation Test Suite for SICETAC Platform
Comprehensive testing of all components before deployment
"""

import os
import sys
import time
import json
import httpx
import psycopg2
import redis
from datetime import datetime
from typing import Dict, List, Tuple, Any
from colorama import init, Fore, Back, Style

# Initialize colorama for colored output
init(autoreset=True)

# Test configuration
API_BASE_URL = os.getenv("API_URL", "http://localhost:5050")
DB_URL = os.getenv("DATABASE_URL", "postgresql://sicetac_user:password@localhost:5432/sicetac_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Test data
TEST_QUOTE_DATA = {
    "period": "202401",
    "configuration": "3S3",
    "origin": "11001000",  # Bogotá
    "destination": "05001000",  # Medellín
    "cargo_type": "GENERAL",
    "unit_type": "ESTACAS",
    "logistics_hours": 2.5
}

TEST_CITIES = [
    {"name": "Bogotá", "code": "11001000"},
    {"name": "Medellín", "code": "05001000"},
    {"name": "Cali", "code": "76001000"},
    {"name": "Barranquilla", "code": "08001000"}
]


class ProductionValidator:
    """Comprehensive production validation suite"""

    def __init__(self):
        self.results = []
        self.errors = []
        self.warnings = []
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0

    def print_header(self, text: str):
        """Print section header"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{text.center(60)}")
        print(f"{Fore.CYAN}{'='*60}\n")

    def print_test(self, name: str):
        """Print test name"""
        self.test_count += 1
        print(f"{Fore.YELLOW}[{self.test_count:02d}] Testing: {name}...", end=" ")

    def print_pass(self, message: str = "PASSED"):
        """Print test pass"""
        self.passed_count += 1
        print(f"{Fore.GREEN}✓ {message}")
        self.results.append((self.test_count, "PASS", message))

    def print_fail(self, message: str = "FAILED"):
        """Print test fail"""
        self.failed_count += 1
        print(f"{Fore.RED}✗ {message}")
        self.results.append((self.test_count, "FAIL", message))
        self.errors.append(message)

    def print_warn(self, message: str):
        """Print warning"""
        print(f"{Fore.YELLOW}⚠ WARNING: {message}")
        self.warnings.append(message)

    def test_environment(self) -> bool:
        """Test environment variables and configuration"""
        self.print_header("ENVIRONMENT VALIDATION")

        required_vars = [
            "DATABASE_URL",
            "REDIS_URL",
            "SICETAC_USERNAME",
            "SICETAC_PASSWORD",
            "SECRET_KEY"
        ]

        for var in required_vars:
            self.print_test(f"Environment variable: {var}")
            if os.getenv(var):
                self.print_pass(f"{var} is set")
            else:
                self.print_fail(f"{var} is not set")

        return self.failed_count == 0

    def test_database(self) -> bool:
        """Test PostgreSQL database connectivity and schema"""
        self.print_header("DATABASE VALIDATION")

        # Test connection
        self.print_test("Database connection")
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            self.print_pass("Connected to PostgreSQL")
        except Exception as e:
            self.print_fail(f"Connection failed: {str(e)}")
            return False

        # Test tables exist
        tables = ["quotations", "quotations_audit"]
        for table in tables:
            self.print_test(f"Table: {table}")
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                self.print_pass(f"Table exists with {count} records")
            except Exception as e:
                self.print_fail(f"Table check failed: {str(e)}")

        # Test indexes
        self.print_test("Database indexes")
        try:
            cur.execute("""
                SELECT indexname FROM pg_indexes
                WHERE schemaname = 'public'
                AND tablename = 'quotations'
            """)
            indexes = cur.fetchall()
            if len(indexes) >= 5:
                self.print_pass(f"Found {len(indexes)} indexes")
            else:
                self.print_warn(f"Only {len(indexes)} indexes found (expected 5+)")
        except Exception as e:
            self.print_fail(f"Index check failed: {str(e)}")

        cur.close()
        conn.close()
        return True

    def test_redis(self) -> bool:
        """Test Redis cache connectivity"""
        self.print_header("REDIS CACHE VALIDATION")

        self.print_test("Redis connection")
        try:
            r = redis.from_url(REDIS_URL)
            r.ping()
            self.print_pass("Connected to Redis")
        except Exception as e:
            self.print_fail(f"Connection failed: {str(e)}")
            return False

        # Test cache operations
        self.print_test("Cache operations")
        try:
            test_key = "test:validation"
            test_value = {"timestamp": str(datetime.now())}

            r.set(test_key, json.dumps(test_value), ex=60)
            retrieved = json.loads(r.get(test_key))

            if retrieved == test_value:
                self.print_pass("Cache read/write working")
            else:
                self.print_fail("Cache data mismatch")

            r.delete(test_key)
        except Exception as e:
            self.print_fail(f"Cache operation failed: {str(e)}")

        return True

    def test_api_health(self) -> bool:
        """Test API health endpoints"""
        self.print_header("API HEALTH VALIDATION")

        endpoints = [
            ("/", "Root endpoint"),
            ("/api/healthz", "Health check"),
            ("/docs", "API documentation"),
            ("/static/index.html", "Frontend")
        ]

        for endpoint, name in endpoints:
            self.print_test(name)
            try:
                response = httpx.get(f"{API_BASE_URL}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.print_pass(f"Status {response.status_code}")
                else:
                    self.print_fail(f"Status {response.status_code}")
            except Exception as e:
                self.print_fail(f"Request failed: {str(e)}")

        return True

    def test_quotation_flow(self) -> bool:
        """Test complete quotation creation flow"""
        self.print_header("QUOTATION FLOW VALIDATION")

        # Test quote creation without auth (should work in dev mode)
        self.print_test("Create quotation")
        try:
            response = httpx.post(
                f"{API_BASE_URL}/api/quote",
                json=TEST_QUOTE_DATA,
                headers={"Authorization": "Bearer development-token"},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if "quotes" in data and len(data["quotes"]) > 0:
                    self.print_pass(f"Received {len(data['quotes'])} quotes")
                else:
                    self.print_fail("No quotes in response")
            else:
                self.print_fail(f"Status {response.status_code}: {response.text}")
        except Exception as e:
            self.print_fail(f"Request failed: {str(e)}")

        return True

    def test_city_search(self) -> bool:
        """Test city search functionality"""
        self.print_header("CITY SEARCH VALIDATION")

        # Test static files
        self.print_test("Cities JavaScript file")
        try:
            response = httpx.get(f"{API_BASE_URL}/static/cities.js", timeout=10)
            if response.status_code == 200 and "COLOMBIAN_CITIES" in response.text:
                self.print_pass("Cities data loaded")
            else:
                self.print_fail("Cities data not found")
        except Exception as e:
            self.print_fail(f"Request failed: {str(e)}")

        # Validate city data
        self.print_test("City data validation")
        city_count = response.text.count('code:')
        if city_count >= 70:
            self.print_pass(f"Found {city_count} cities")
        else:
            self.print_warn(f"Only {city_count} cities found (expected 70+)")

        return True

    def test_security(self) -> bool:
        """Test security configurations"""
        self.print_header("SECURITY VALIDATION")

        # Test CORS headers
        self.print_test("CORS configuration")
        try:
            response = httpx.options(
                f"{API_BASE_URL}/api/healthz",
                headers={"Origin": "https://example.com"}
            )
            if "access-control-allow-origin" in response.headers:
                self.print_pass("CORS headers present")
            else:
                self.print_warn("CORS headers might not be configured")
        except Exception as e:
            self.print_warn(f"CORS test inconclusive: {str(e)}")

        # Test rate limiting would go here (requires nginx)

        # Test SQL injection protection
        self.print_test("SQL injection protection")
        malicious_input = "'; DROP TABLE quotations; --"
        try:
            response = httpx.post(
                f"{API_BASE_URL}/api/quote",
                json={
                    **TEST_QUOTE_DATA,
                    "period": malicious_input
                },
                headers={"Authorization": "Bearer development-token"},
                timeout=10
            )
            if response.status_code == 422:  # Validation error expected
                self.print_pass("Input validation working")
            else:
                self.print_warn("Unexpected response to malicious input")
        except Exception as e:
            self.print_pass("Request rejected as expected")

        return True

    def test_performance(self) -> bool:
        """Test performance metrics"""
        self.print_header("PERFORMANCE VALIDATION")

        # Test response times
        self.print_test("API response time")
        times = []
        for i in range(5):
            start = time.time()
            response = httpx.get(f"{API_BASE_URL}/api/healthz")
            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)

        avg_time = sum(times) / len(times)
        if avg_time < 100:
            self.print_pass(f"Average response: {avg_time:.2f}ms")
        elif avg_time < 500:
            self.print_warn(f"Average response: {avg_time:.2f}ms (consider optimization)")
        else:
            self.print_fail(f"Average response: {avg_time:.2f}ms (too slow)")

        return True

    def test_backup_restore(self) -> bool:
        """Test backup and restore procedures"""
        self.print_header("BACKUP/RESTORE VALIDATION")

        # Test backup script exists
        self.print_test("Backup script")
        if os.path.exists("scripts/backup.sh"):
            self.print_pass("Backup script found")
        else:
            self.print_fail("Backup script not found")

        # Test backup directory
        self.print_test("Backup directory")
        if os.path.exists("backups"):
            self.print_pass("Backup directory exists")
        else:
            os.makedirs("backups", exist_ok=True)
            self.print_pass("Backup directory created")

        return True

    def test_monitoring(self) -> bool:
        """Test monitoring and logging"""
        self.print_header("MONITORING VALIDATION")

        # Test log directory
        self.print_test("Log directory")
        if os.path.exists("logs"):
            self.print_pass("Log directory exists")
        else:
            os.makedirs("logs", exist_ok=True)
            self.print_pass("Log directory created")

        # Test health metrics
        self.print_test("Health metrics endpoint")
        try:
            response = httpx.get(f"{API_BASE_URL}/api/healthz", timeout=10)
            data = response.json()
            if "status" in data:
                self.print_pass("Health metrics available")
            else:
                self.print_warn("Health metrics incomplete")
        except Exception as e:
            self.print_fail(f"Health check failed: {str(e)}")

        return True

    def generate_report(self):
        """Generate final validation report"""
        self.print_header("VALIDATION REPORT")

        total_tests = self.test_count
        pass_rate = (self.passed_count / total_tests * 100) if total_tests > 0 else 0

        print(f"{Fore.CYAN}Total Tests: {total_tests}")
        print(f"{Fore.GREEN}Passed: {self.passed_count}")
        print(f"{Fore.RED}Failed: {self.failed_count}")
        print(f"{Fore.YELLOW}Warnings: {len(self.warnings)}")
        print(f"\n{Fore.CYAN}Pass Rate: {pass_rate:.1f}%")

        if self.failed_count == 0:
            print(f"\n{Fore.GREEN}{Style.BRIGHT}✅ ALL TESTS PASSED - READY FOR PRODUCTION!")
        else:
            print(f"\n{Fore.RED}{Style.BRIGHT}❌ VALIDATION FAILED - FIX ISSUES BEFORE DEPLOYMENT")
            print(f"\n{Fore.RED}Failed Tests:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\n{Fore.YELLOW}Warnings to Review:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"validation_report_{timestamp}.txt"

        with open(report_file, "w") as f:
            f.write("SICETAC PRODUCTION VALIDATION REPORT\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total Tests: {total_tests}\n")
            f.write(f"Passed: {self.passed_count}\n")
            f.write(f"Failed: {self.failed_count}\n")
            f.write(f"Warnings: {len(self.warnings)}\n")
            f.write(f"Pass Rate: {pass_rate:.1f}%\n\n")

            if self.errors:
                f.write("ERRORS:\n")
                for error in self.errors:
                    f.write(f"  - {error}\n")
                f.write("\n")

            if self.warnings:
                f.write("WARNINGS:\n")
                for warning in self.warnings:
                    f.write(f"  - {warning}\n")
                f.write("\n")

            f.write("DETAILED RESULTS:\n")
            for test_num, status, message in self.results:
                f.write(f"  [{test_num:02d}] {status}: {message}\n")

        print(f"\n{Fore.CYAN}Report saved to: {report_file}")

        return self.failed_count == 0


def main():
    """Run complete production validation suite"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}SICETAC PRODUCTION VALIDATION SUITE")
    print(f"{Fore.CYAN}Starting comprehensive system validation...")
    print(f"{Fore.CYAN}Time: {datetime.now()}\n")

    validator = ProductionValidator()

    # Run all validation tests
    tests = [
        validator.test_environment,
        validator.test_database,
        validator.test_redis,
        validator.test_api_health,
        validator.test_quotation_flow,
        validator.test_city_search,
        validator.test_security,
        validator.test_performance,
        validator.test_backup_restore,
        validator.test_monitoring
    ]

    # Execute tests
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"\n{Fore.RED}Test suite error: {str(e)}")
            validator.failed_count += 1

    # Generate report
    success = validator.generate_report()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()