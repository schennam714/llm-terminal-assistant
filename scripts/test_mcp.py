#!/usr/bin/env python3
"""
Simple test script for the MCP server
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🧪 Testing MCP Server...")
    
    try:
        # Import our MCP server module
        from mcp_server.mcp_server import platform_adapter
        
        # Test system info
        print("\n1. Testing system information...")
        success, stdout, stderr = platform_adapter.execute_command("pwd")
        print(f"   Current directory: {stdout if success else stderr}")
        
        # Test command validation
        print("\n2. Testing command validation...")
        is_valid, msg = platform_adapter.validate_command("ls -la")
        print(f"   'ls -la' validation: {is_valid} - {msg}")
        
        is_valid, msg = platform_adapter.validate_command("rm -rf /")
        print(f"   'rm -rf /' validation: {is_valid} - {msg}")
        
        # Test platform adaptation
        print("\n3. Testing platform adaptation...")
        adapted = platform_adapter.adapt_command("ls")
        print(f"   'ls' adapted to: '{adapted}'")
        
        # Test safe command execution
        print("\n4. Testing safe command execution...")
        success, stdout, stderr = platform_adapter.execute_command("echo 'Hello from MCP!'")
        if success:
            print(f"   Echo test: ✅ {stdout}")
        else:
            print(f"   Echo test: ❌ {stderr}")
        
        print("\n✅ MCP Server tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 