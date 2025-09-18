#!/usr/bin/env python3
"""
Example usage of NASA TechTransfer API with PyASAN.

This example demonstrates how to use the TechTransferClient to search for
NASA patents, software, and spinoff technologies.
"""

from pyasan import TechTransferClient
from pyasan.exceptions import PyASANError, ValidationError, APIError


def main():
    """Demonstrate TechTransfer API functionality."""
    # Initialize client (uses NASA_API_KEY env var by default)
    client = TechTransferClient()
    
    # Or provide API key directly
    # client = TechTransferClient(api_key="your_api_key_here")

    try:
        print("=== NASA TechTransfer API Examples ===\n")

        # Example 1: Search for patents
        print("1. Searching for patents related to 'solar energy'...")
        patents = client.search_patents(query="solar energy", limit=3)
        
        if len(patents) > 0:
            print(f"Found {len(patents)} patent(s):")
            for i, patent in enumerate(patents.results[:2], 1):  # Show first 2
                print(f"\n  {i}. {patent.title}")
                if patent.patent_number:
                    print(f"     Patent Number: {patent.patent_number}")
                if patent.center:
                    print(f"     NASA Center: {patent.center}")
                if patent.abstract:
                    abstract = patent.abstract[:200] + "..." if len(patent.abstract) > 200 else patent.abstract
                    print(f"     Abstract: {abstract}")
        else:
            print("No patents found.")

        print("\n" + "="*60 + "\n")

        # Example 2: Search for software
        print("2. Searching for software related to 'machine learning'...")
        software_list = client.search_software(query="machine learning", limit=3)
        
        if len(software_list) > 0:
            print(f"Found {len(software_list)} software item(s):")
            for i, software in enumerate(software_list.results[:2], 1):  # Show first 2
                print(f"\n  {i}. {software.title}")
                if software.version:
                    print(f"     Version: {software.version}")
                if software.center:
                    print(f"     NASA Center: {software.center}")
                if software.language:
                    print(f"     Language: {software.language}")
                if software.description:
                    desc = software.description[:200] + "..." if len(software.description) > 200 else software.description
                    print(f"     Description: {desc}")
        else:
            print("No software found.")

        print("\n" + "="*60 + "\n")

        # Example 3: Search for spinoffs
        print("3. Searching for spinoffs related to 'medical'...")
        spinoffs = client.search_spinoffs(query="medical", limit=3)
        
        if len(spinoffs) > 0:
            print(f"Found {len(spinoffs)} spinoff(s):")
            for i, spinoff in enumerate(spinoffs.results[:2], 1):  # Show first 2
                print(f"\n  {i}. {spinoff.title}")
                if spinoff.company:
                    print(f"     Company: {spinoff.company}")
                if spinoff.state:
                    print(f"     State: {spinoff.state}")
                if spinoff.publication_year:
                    print(f"     Year: {spinoff.publication_year}")
                if spinoff.description:
                    desc = spinoff.description[:200] + "..." if len(spinoff.description) > 200 else spinoff.description
                    print(f"     Description: {desc}")
        else:
            print("No spinoffs found.")

        print("\n" + "="*60 + "\n")

        # Example 4: Search across all categories
        print("4. Searching all categories for 'robotics'...")
        all_results = client.search_all(query="robotics", limit=2)
        
        for category, results in all_results.items():
            if category.endswith("_error"):
                print(f"Error in {category.replace('_error', '')}: {results}")
                continue
                
            print(f"\n{category.upper()}:")
            if hasattr(results, 'results') and len(results.results) > 0:
                for item in results.results[:1]:  # Show first result from each category
                    print(f"  • {item.title}")
            else:
                print("  No results found.")

        print("\n" + "="*60 + "\n")

        # Example 5: Get available categories
        print("5. Available TechTransfer categories:")
        categories = client.get_categories()
        for category in categories:
            print(f"  • {category}")

    except ValidationError as e:
        print(f"Validation Error: {e}")
    except APIError as e:
        print(f"API Error: {e}")
    except PyASANError as e:
        print(f"PyASAN Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
