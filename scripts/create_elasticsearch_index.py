#!/usr/bin/env python3
"""
Create Elasticsearch Index for News Articles

This script creates the Elasticsearch index with the proper mapping
for storing published news articles.
"""

import json
import os
import sys
from pathlib import Path
from elasticsearch import Elasticsearch
from dotenv import dotenv_values

# Load environment variables
env_config = dotenv_values('.env')
if env_config:
    for key, value in env_config.items():
        if value and not os.getenv(key):
            os.environ[key] = value


def create_index(force: bool = False):
    """Create the Elasticsearch index with proper mapping.

    Args:
        force: If True, delete and recreate existing index without prompting.
    """

    # Get configuration from environment
    es_endpoint = os.getenv("ELASTICSEARCH_ENDPOINT")
    es_api_key = os.getenv("ELASTICSEARCH_API_KEY")
    index_name = os.getenv("ELASTIC_ARCHIVIST_INDEX", "news_archive")

    if not es_endpoint:
        print("❌ Error: ELASTICSEARCH_ENDPOINT not set in environment")
        print("   Please set it in your .env file")
        sys.exit(1)

    if not es_api_key:
        print("❌ Error: ELASTICSEARCH_API_KEY not set in environment")
        print("   Please set it in your .env file")
        sys.exit(1)

    print("🔌 Connecting to Elasticsearch...")
    print(f"   Endpoint: {es_endpoint}")
    print(f"   Index: {index_name}")

    # Create Elasticsearch client
    es = Elasticsearch(
        es_endpoint,
        api_key=es_api_key
    )

    # Test connection and detect Serverless
    is_serverless = False
    try:
        info = es.info()
        version = info['version']['number']
        build_flavor = info['version'].get('build_flavor', '')
        is_serverless = build_flavor == 'serverless'
        print(f"✅ Connected to Elasticsearch")
        print(f"   Version: {version}")
        print(f"   Cluster: {info['cluster_name']}")
        if is_serverless:
            print(f"   Mode: Serverless")
    except Exception as e:
        print(f"❌ Failed to connect to Elasticsearch: {e}")
        sys.exit(1)

    # Load mapping from JSON file
    mapping_file = Path(__file__).parent.parent / "docs" / "elasticsearch-index-mapping.json"

    if not mapping_file.exists():
        print(f"❌ Mapping file not found: {mapping_file}")
        sys.exit(1)

    print(f"\n📄 Loading mapping from: {mapping_file}")
    with open(mapping_file, 'r') as f:
        index_config = json.load(f)

    # Create ILM policy for article lifecycle management (not available on Serverless)
    if is_serverless:
        print(f"\n📋 Skipping ILM policy (not available on Serverless)")
    else:
        ilm_policy_name = f"{index_name}-lifecycle"
        print(f"\n📋 Setting up ILM policy: {ilm_policy_name}")
        try:
            es.ilm.put_lifecycle(
                name=ilm_policy_name,
                policy={
                    "phases": {
                        "hot": {
                            "min_age": "0ms",
                            "actions": {
                                "set_priority": {"priority": 100}
                            }
                        },
                        "warm": {
                            "min_age": "30d",
                            "actions": {
                                "set_priority": {"priority": 50},
                                "forcemerge": {"max_num_segments": 1},
                                "readonly": {}
                            }
                        },
                        "cold": {
                            "min_age": "90d",
                            "actions": {
                                "set_priority": {"priority": 0}
                            }
                        }
                    }
                }
            )
            print(f"✅ ILM policy '{ilm_policy_name}' created")
            # Add ILM policy to index settings
            index_config.setdefault("settings", {}).setdefault("index", {})
            index_config["settings"]["index"]["lifecycle.name"] = ilm_policy_name
        except Exception as e:
            print(f"⚠️  ILM policy creation skipped (may require license): {e}")

    # Check if index already exists
    if es.indices.exists(index=index_name):
        print(f"\n⚠️  Index '{index_name}' already exists!")
        if force:
            print(f"🗑️  Deleting existing index '{index_name}' (--force)...")
            es.indices.delete(index=index_name)
            print("✅ Index deleted")
        else:
            response = input("   Do you want to delete and recreate it? (yes/no): ")
            if response.lower() in ['yes', 'y']:
                print(f"🗑️  Deleting existing index '{index_name}'...")
                es.indices.delete(index=index_name)
                print("✅ Index deleted")
            else:
                print("❌ Aborted. Index not modified.")
                sys.exit(0)

    # Strip shard/replica settings on Serverless (not supported)
    settings = index_config.get("settings", {})
    if is_serverless:
        idx_settings = settings.get("index", {})
        idx_settings.pop("number_of_shards", None)
        idx_settings.pop("number_of_replicas", None)
        # Remove empty index dict to avoid issues
        if not idx_settings:
            settings.pop("index", None)

    # Create the index (using keyword args - body= is deprecated in ES Python client 8.x+)
    print(f"\n📦 Creating index '{index_name}'...")
    try:
        es.indices.create(
            index=index_name,
            settings=settings,
            mappings=index_config.get("mappings", {})
        )
        print(f"✅ Index '{index_name}' created successfully!")
    except Exception as e:
        print(f"❌ Failed to create index: {e}")
        sys.exit(1)

    # Verify index creation
    print(f"\n🔍 Verifying index creation...")
    mapping = es.indices.get_mapping(index=index_name)
    idx_settings = es.indices.get_settings(index=index_name)

    print(f"✅ Index verified:")
    index_detail = idx_settings[index_name]['settings']['index']
    if not is_serverless:
        shards = index_detail.get('number_of_shards', 'default')
        replicas = index_detail.get('number_of_replicas', 'default')
        print(f"   Shards: {shards}")
        print(f"   Replicas: {replicas}")
    else:
        print(f"   Mode: Serverless (shards managed automatically)")

    field_count = len(mapping[index_name]['mappings']['properties'])
    print(f"   Mapped fields: {field_count}")

    # Display key fields
    print(f"\n📋 Key fields configured:")
    key_fields = [
        "story_id", "headline", "content", "topic", "word_count",
        "published_at", "status", "research_data", "editorial_review"
    ]
    for field in key_fields:
        props = mapping[index_name]['mappings']['properties']
        if field in props:
            field_type = props[field].get('type', 'object')
            print(f"   - {field}: {field_type}")

    print(f"\n🎉 Index setup complete!")
    print(f"\n💡 You can now publish articles to this index using the Publisher agent")
    print(f"💡 The Archivist agent will search this index for historical articles")


if __name__ == "__main__":
    print("📰 Elastic News - Index Creation Script")
    print("=" * 60)
    print()

    force = "--force" in sys.argv or "-f" in sys.argv

    try:
        create_index(force=force)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
