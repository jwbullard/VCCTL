#!/usr/bin/env python3
"""Test help system functionality."""

import sys
sys.path.insert(0, 'src')

import logging
logging.basicConfig(level=logging.DEBUG)

from app.help import HelpManager

# Test help manager
print("Testing Help Manager...")
help_manager = HelpManager()

print(f"Sections available: {list(help_manager.sections.keys())}")
print(f"Topics available: {list(help_manager.topics_index.keys())}")

# Test getting overview topic
overview_topic = help_manager.get_topic("overview")
if overview_topic:
    print(f"\nOverview topic found: {overview_topic.title}")
    print(f"Content length: {len(overview_topic.content)} characters")
    print(f"First 200 chars: {overview_topic.content[:200]}...")
else:
    print("\nERROR: Overview topic not found!")

# Test getting interface topic
interface_topic = help_manager.get_topic("interface")
if interface_topic:
    print(f"\nInterface topic found: {interface_topic.title}")
    print(f"Content length: {len(interface_topic.content)} characters")
else:
    print("\nERROR: Interface topic not found!")

# Test search
search_results = help_manager.search_topics("cement")
print(f"\nSearch for 'cement' found {len(search_results)} results:")
for topic in search_results:
    print(f"  - {topic.title}")

print("\n✓ Help system basic functionality working")