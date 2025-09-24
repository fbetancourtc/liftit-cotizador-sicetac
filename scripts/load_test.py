#!/usr/bin/env python3
"""
Load Testing Script for SICETAC Platform
Tests system performance under various load conditions
"""

import asyncio
import time
import random
import statistics
from datetime import datetime
from typing import List, Dict, Any
import httpx
import json
from concurrent.futures import ThreadPoolExecutor
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Configuration
API_BASE_URL = "http://localhost:5050"
AUTH_TOKEN = "Bearer development-token"

# Load test scenarios
LOAD_SCENARIOS = {
    "light": {
        "users": 10,
        "duration": 30,
        "ramp_up": 5,
        "description": "Light load - 10 concurrent users"
    },
    "moderate": {
        "users": 50,
        "duration": 60,
        "ramp_up": 10,
        "description": "Moderate load - 50 concurrent users"
    },
    "heavy": {
        "users": 100,
        "duration": 120,
        "ramp_up": 20,
        "description": "Heavy load - 100 concurrent users"
    },
    "stress": {
        "users": 200,
        "duration": 180,
        "ramp_up": 30,
        "description": "Stress test - 200 concurrent users"
    }
}

# Test data variations
CITIES = [
    ("11001000", "05001000"),  # Bogotá to Medellín
    ("76001000", "08001000"),  # Cali to Barranquilla
    ("05001000", "13001000"),  # Medellín to Cartagena
    ("68001000", "54001000"),  # Bucaramanga to Cúcuta
    ("66001000", "17001000"),  # Pereira to Manizales
]

CONFIGURATIONS = ["2", "3", "2S2", "2S3", "3S2", "3S3"]
CARGO_TYPES = ["GENERAL", "CONTENEDOR", "CARGA REFRIGERADA", "GRANEL SÓLIDO"]
UNIT_TYPES = ["ESTACAS", "TRAYLER", "TERMOKING"]


class LoadTester:
    """Load testing class for SICETAC platform"""

    def __init__(self, scenario: str = "light"):
        self.scenario = LOAD_SCENARIOS.get(scenario, LOAD_SCENARIOS["light"])
        self.results = {
            "requests": [],
            "errors": [],
            "response_times": [],
            "status_codes": {},
            "start_time": None,
            "end_time": None
        }
        self.active_users = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    def generate_random_quote_request(self) -> Dict[str, Any]:
        """Generate random quote request data"""
        origin, destination = random.choice(CITIES)
        return {
            "period": f"2024{random.randint(1, 12):02d}",
            "configuration": random.choice(CONFIGURATIONS),
            "origin": origin,
            "destination": destination,
            "cargo_type": random.choice(CARGO_TYPES),
            "unit_type": random.choice(UNIT_TYPES),
            "logistics_hours": round(random.uniform(0, 10), 1)
        }

    async def make_request(self, client: httpx.AsyncClient, endpoint: str, data: Dict = None) -> Dict:
        """Make a single request and record metrics"""
        start_time = time.time()
        request_result = {
            "endpoint": endpoint,
            "start_time": start_time,
            "success": False,
            "status_code": None,
            "response_time": None,
            "error": None
        }

        try:
            if data:
                response = await client.post(
                    f"{API_BASE_URL}{endpoint}",
                    json=data,
                    headers={"Authorization": AUTH_TOKEN},
                    timeout=30
                )
            else:
                response = await client.get(
                    f"{API_BASE_URL}{endpoint}",
                    headers={"Authorization": AUTH_TOKEN},
                    timeout=30
                )

            request_result["response_time"] = (time.time() - start_time) * 1000  # ms
            request_result["status_code"] = response.status_code
            request_result["success"] = response.status_code == 200

            # Track status codes
            status = str(response.status_code)
            self.results["status_codes"][status] = self.results["status_codes"].get(status, 0) + 1

            if request_result["success"]:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                request_result["error"] = f"HTTP {response.status_code}"

        except Exception as e:
            request_result["response_time"] = (time.time() - start_time) * 1000
            request_result["error"] = str(e)
            self.failed_requests += 1
            self.results["errors"].append(str(e))

        self.total_requests += 1
        self.results["requests"].append(request_result)
        self.results["response_times"].append(request_result["response_time"])

        return request_result

    async def user_session(self, user_id: int):
        """Simulate a user session"""
        async with httpx.AsyncClient() as client:
            self.active_users += 1
            print(f"{Fore.GREEN}User {user_id} started (Active: {self.active_users})")

            session_start = time.time()
            while time.time() - self.results["start_time"] < self.scenario["duration"]:
                # Random action selection
                action = random.choice([
                    "health_check",
                    "create_quote",
                    "create_quote",  # Higher probability
                    "create_quote",
                    "list_quotes"
                ])

                if action == "health_check":
                    await self.make_request(client, "/api/healthz")
                elif action == "create_quote":
                    quote_data = self.generate_random_quote_request()
                    await self.make_request(client, "/api/quote", quote_data)
                elif action == "list_quotes":
                    await self.make_request(client, "/api/quotes/")

                # Random think time between requests (1-5 seconds)
                await asyncio.sleep(random.uniform(1, 5))

            self.active_users -= 1
            print(f"{Fore.YELLOW}User {user_id} finished (Active: {self.active_users})")

    async def run_load_test(self):
        """Run the load test scenario"""
        print(f"\n{Fore.CYAN}{Style.BRIGHT}LOAD TEST: {self.scenario['description']}")
        print(f"{Fore.CYAN}Duration: {self.scenario['duration']}s")
        print(f"{Fore.CYAN}Target Users: {self.scenario['users']}")
        print(f"{Fore.CYAN}Ramp-up: {self.scenario['ramp_up']}s\n")

        self.results["start_time"] = time.time()

        # Create user tasks with ramp-up
        tasks = []
        ramp_up_delay = self.scenario["ramp_up"] / self.scenario["users"]

        for i in range(self.scenario["users"]):
            task = asyncio.create_task(self.user_session(i + 1))
            tasks.append(task)
            await asyncio.sleep(ramp_up_delay)

        # Wait for all users to complete
        await asyncio.gather(*tasks)
        self.results["end_time"] = time.time()

    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.results["response_times"]:
            return {}

        response_times = self.results["response_times"]
        duration = self.results["end_time"] - self.results["start_time"]

        # Calculate percentiles
        sorted_times = sorted(response_times)
        p50 = sorted_times[int(len(sorted_times) * 0.50)]
        p75 = sorted_times[int(len(sorted_times) * 0.75)]
        p90 = sorted_times[int(len(sorted_times) * 0.90)]
        p95 = sorted_times[int(len(sorted_times) * 0.95)]
        p99 = sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 100 else sorted_times[-1]

        metrics = {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0,
            "requests_per_second": self.total_requests / duration if duration > 0 else 0,
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "mean_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "stdev_response_time": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "p50": p50,
            "p75": p75,
            "p90": p90,
            "p95": p95,
            "p99": p99,
            "test_duration": duration
        }

        return metrics

    def print_report(self):
        """Print load test report"""
        metrics = self.calculate_metrics()

        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{'LOAD TEST RESULTS'.center(60)}")
        print(f"{Fore.CYAN}{'='*60}\n")

        print(f"{Fore.GREEN}Summary:")
        print(f"  Total Requests: {metrics.get('total_requests', 0)}")
        print(f"  Successful: {metrics.get('successful_requests', 0)}")
        print(f"  Failed: {metrics.get('failed_requests', 0)}")
        print(f"  Success Rate: {metrics.get('success_rate', 0):.2f}%")
        print(f"  Duration: {metrics.get('test_duration', 0):.2f}s")
        print(f"  Requests/sec: {metrics.get('requests_per_second', 0):.2f}")

        print(f"\n{Fore.YELLOW}Response Times (ms):")
        print(f"  Min: {metrics.get('min_response_time', 0):.2f}")
        print(f"  Max: {metrics.get('max_response_time', 0):.2f}")
        print(f"  Mean: {metrics.get('mean_response_time', 0):.2f}")
        print(f"  Median: {metrics.get('median_response_time', 0):.2f}")
        print(f"  Std Dev: {metrics.get('stdev_response_time', 0):.2f}")

        print(f"\n{Fore.CYAN}Percentiles (ms):")
        print(f"  50th: {metrics.get('p50', 0):.2f}")
        print(f"  75th: {metrics.get('p75', 0):.2f}")
        print(f"  90th: {metrics.get('p90', 0):.2f}")
        print(f"  95th: {metrics.get('p95', 0):.2f}")
        print(f"  99th: {metrics.get('p99', 0):.2f}")

        if self.results["status_codes"]:
            print(f"\n{Fore.MAGENTA}Status Codes:")
            for code, count in sorted(self.results["status_codes"].items()):
                percentage = (count / self.total_requests * 100) if self.total_requests > 0 else 0
                print(f"  {code}: {count} ({percentage:.1f}%)")

        if self.results["errors"]:
            print(f"\n{Fore.RED}Errors (first 5):")
            for error in self.results["errors"][:5]:
                print(f"  - {error}")

        # Performance assessment
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}{'PERFORMANCE ASSESSMENT'.center(60)}")
        print(f"{Fore.CYAN}{'='*60}\n")

        if metrics.get('success_rate', 0) >= 99:
            print(f"{Fore.GREEN}✅ EXCELLENT: Success rate above 99%")
        elif metrics.get('success_rate', 0) >= 95:
            print(f"{Fore.YELLOW}⚠ GOOD: Success rate above 95%")
        else:
            print(f"{Fore.RED}❌ POOR: Success rate below 95%")

        if metrics.get('p95', float('inf')) < 1000:
            print(f"{Fore.GREEN}✅ EXCELLENT: 95th percentile under 1 second")
        elif metrics.get('p95', float('inf')) < 3000:
            print(f"{Fore.YELLOW}⚠ ACCEPTABLE: 95th percentile under 3 seconds")
        else:
            print(f"{Fore.RED}❌ SLOW: 95th percentile over 3 seconds")

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"load_test_report_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump({
                "scenario": self.scenario,
                "metrics": metrics,
                "status_codes": self.results["status_codes"],
                "timestamp": timestamp
            }, f, indent=2)

        print(f"\n{Fore.CYAN}Report saved to: {report_file}")


async def main():
    """Main function to run load tests"""
    import sys

    # Parse command line arguments
    scenario = sys.argv[1] if len(sys.argv) > 1 else "light"

    if scenario not in LOAD_SCENARIOS:
        print(f"{Fore.RED}Invalid scenario. Available: {', '.join(LOAD_SCENARIOS.keys())}")
        sys.exit(1)

    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/healthz", timeout=5)
            if response.status_code != 200:
                print(f"{Fore.RED}Server health check failed. Is the server running?")
                sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Cannot connect to server at {API_BASE_URL}")
        print(f"Error: {str(e)}")
        sys.exit(1)

    # Run load test
    tester = LoadTester(scenario)
    await tester.run_load_test()
    tester.print_report()


if __name__ == "__main__":
    print(f"\n{Fore.CYAN}{Style.BRIGHT}SICETAC LOAD TESTING TOOL")
    print(f"{Fore.CYAN}Testing: {API_BASE_URL}")
    asyncio.run(main())