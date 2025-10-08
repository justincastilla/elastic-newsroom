#!/usr/bin/env python3
"""
Test Elasticsearch Index Creation

This test creates a temporary test index, verifies it was created correctly,
then cleans it up by deleting it.
"""

import json
import os
import sys
from pathlib import Path
from elasticsearch import Elasticsearch
from dotenv import dotenv_values

# Add parent directory to path to import from scripts
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
env_config = dotenv_values('.env')
if env_config:
    for key, value in env_config.items():
        if value and not os.getenv(key):
            os.environ[key] = value


def test_elasticsearch_index():
    """Test index creation and cleanup"""

    print("🧪 Elastic News - Elasticsearch Index Test")
    print("=" * 60)
    print()

    # Get configuration from environment
    es_endpoint = os.getenv("ELASTICSEARCH_ENDPOINT")
    es_api_key = os.getenv("ELASTIC_SEARCH_API_KEY")
    test_index_name = "news_archive_test"

    if not es_endpoint:
        print("❌ Error: ELASTICSEARCH_ENDPOINT not set in environment")
        print("   Please set it in your .env file")
        sys.exit(1)

    if not es_api_key:
        print("❌ Error: ELASTIC_SEARCH_API_KEY not set in environment")
        print("   Please set it in your .env file")
        sys.exit(1)

    print("🔌 Connecting to Elasticsearch...")
    print(f"   Endpoint: {es_endpoint}")
    print(f"   Test Index: {test_index_name}")
    print()

    # Create Elasticsearch client
    es = Elasticsearch(
        es_endpoint,
        api_key=es_api_key
    )

    # Test connection
    try:
        info = es.info()
        print(f"✅ Connected to Elasticsearch")
        print(f"   Version: {info['version']['number']}")
        print(f"   Cluster: {info['cluster_name']}")
        print()
    except Exception as e:
        print(f"❌ Failed to connect to Elasticsearch: {e}")
        sys.exit(1)

    # Load mapping from JSON file
    mapping_file = Path(__file__).parent.parent / "docs" / "elasticsearch-index-mapping.json"

    if not mapping_file.exists():
        print(f"❌ Mapping file not found: {mapping_file}")
        sys.exit(1)

    print(f"📄 Loading mapping from: {mapping_file}")
    with open(mapping_file, 'r') as f:
        index_config = json.load(f)
    print()

    # Clean up test index if it already exists
    if es.indices.exists(index=test_index_name):
        print(f"⚠️  Test index '{test_index_name}' already exists, deleting...")
        es.indices.delete(index=test_index_name)
        print("✅ Old test index deleted")
        print()

    # Create the test index
    print(f"📦 Creating test index '{test_index_name}'...")
    try:
        es.indices.create(
            index=test_index_name,
            body=index_config
        )
        print(f"✅ Test index created successfully!")
        print()
    except Exception as e:
        print(f"❌ Failed to create test index: {e}")
        sys.exit(1)

    # Verify index creation
    print(f"🔍 Verifying test index...")
    try:
        mapping = es.indices.get_mapping(index=test_index_name)

        print(f"✅ Index verified:")

        field_count = len(mapping[test_index_name]['mappings']['properties'])
        print(f"   Mapped fields: {field_count}")
        print()

        # Verify key fields exist
        print("📋 Verifying key fields...")
        key_fields = [
            "story_id", "headline", "content", "topic", "word_count",
            "published_at", "status", "research_data", "editorial_review"
        ]

        missing_fields = []
        for field in key_fields:
            if field in mapping[test_index_name]['mappings']['properties']:
                field_def = mapping[test_index_name]['mappings']['properties'][field]
                # Some fields are objects and don't have a direct 'type'
                field_type = field_def.get('type', 'object')
                print(f"   ✓ {field}: {field_type}")
            else:
                missing_fields.append(field)
                print(f"   ✗ {field}: MISSING")

        if missing_fields:
            print(f"\n❌ Test failed: Missing fields: {missing_fields}")
            # Still clean up even on failure
            print(f"\n🗑️  Cleaning up test index...")
            es.indices.delete(index=test_index_name)
            sys.exit(1)

        print()
        print("✅ All key fields verified!")

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        # Try to clean up even on failure
        try:
            es.indices.delete(index=test_index_name)
        except:
            pass
        sys.exit(1)

    # Clean up: Delete test index
    print()
    print(f"🗑️  Cleaning up test index '{test_index_name}'...")
    try:
        es.indices.delete(index=test_index_name)
        print(f"✅ Test index deleted successfully!")
        print()
    except Exception as e:
        print(f"❌ Failed to delete test index: {e}")
        print(f"⚠️  You may need to manually delete the index '{test_index_name}'")
        sys.exit(1)

    # Final verification - ensure it's gone
    print("🔍 Verifying test index cleanup...")
    if not es.indices.exists(index=test_index_name):
        print("✅ Test index successfully removed")
    else:
        print("❌ Test index still exists after deletion!")
        sys.exit(1)

    print()
    print("=" * 60)
    print("🎉 ELASTICSEARCH INDEX TEST PASSED")
    print("=" * 60)
    print()
    print("✅ Test index created successfully")
    print("✅ All fields verified")
    print("✅ Test index cleaned up")
    print()


if __name__ == "__main__":
    try:
        test_elasticsearch_index()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
