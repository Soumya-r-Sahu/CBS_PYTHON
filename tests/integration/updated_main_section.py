# Modified main section for cross_framework_compatibility_test.py

if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Cross-framework compatibility tests")
    parser.add_argument("--api-url", help="API URL to test against")
    parser.add_argument("--method", choices=["simple", "unittest", "both"], default="both",
                        help="Test method to use: simple, unittest, or both")
    args = parser.parse_args()
    
    # Get API URL from arguments or config
    api_config = get_api_config()
    default_url = f"http://{api_config['host']}:{api_config['port']}/api/v1"
    api_url = args.api_url or os.environ.get('CBS_TEST_API_URL') or default_url
    
    # Run the tests based on selected method
    if args.method in ["simple", "both"]:
        print("\n====== RUNNING SIMPLE COMPATIBILITY TESTS ======\n")
        print(f"Testing cross-framework compatibility with API at: {api_url}")
        
        # Run tests for all frameworks
        results = test_all_frameworks(api_url)
        
        # Print results
        print("\nSimple Test Results:")
        print("===================")
        
        for framework, result in results.items():
            success = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{framework.upper()}: {success}")
            
            # Print details of failed tests
            if not result["success"]:
                for test_name, test_result in result.items():
                    if isinstance(test_result, dict) and "success" in test_result and not test_result["success"]:
                        print(f"  - {test_name}: {test_result['message']}")
        
        # Save results to file
        output_file = os.path.join(project_root, "compatibility_test_results.json")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
    
    if args.method in ["unittest", "both"]:
        print("\n====== RUNNING UNITTEST COMPATIBILITY TESTS ======\n")
        # Set the API URL as an environment variable for the unittest tests
        os.environ['CBS_TEST_API_URL'] = api_url
        
        # Run unittest tests
        run_unittest_tests()
