#!/usr/bin/env python3
"""
Test the exact line splitting logic used in the monitoring code.
"""

def test_line_splitting():
    """Test how the file content is split into lines."""
    print("🔍 Testing Line Splitting Logic")
    print("=" * 50)
    
    # Read the actual file content exactly like the monitoring code does
    stdout_path = "Operations/YAP03/proc_1755983544638_stdout.txt"
    
    try:
        with open(stdout_path, 'r', encoding='utf-8') as f:
            new_content = f.read()
            
            print(f"Raw content length: {len(new_content)} characters")
            print(f"Content repr: {repr(new_content[:100])}...")
            
            # Test the exact splitting logic from the monitoring code
            lines = new_content.strip().split('\n')
            
            print(f"Number of lines after split: {len(lines)}")
            
            for i, line in enumerate(lines, 1):
                print(f"Line {i}: {repr(line[:80])}...")
                if line.strip():
                    if line.startswith("GENMIC_PROGRESS:"):
                        print(f"  ✅ Valid GENMIC_PROGRESS line")
                    else:
                        print(f"  ❌ Not a GENMIC_PROGRESS line")
                else:
                    print(f"  ⚠️  Empty line")
            
            print(f"\nTotal non-empty lines: {sum(1 for line in lines if line.strip())}")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    test_line_splitting()