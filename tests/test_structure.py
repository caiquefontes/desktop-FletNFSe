"""
Test script to verify basic project structure and imports
"""

def test_imports():
    """Test that all modules can be imported successfully."""
    try:
        # Test models
        from models.models import NFSe, PedidoCompra, SapLancamento, initialize_database
        print("Models imported successfully")
        
        # Test miniapp modules can be imported (without running them)
        import apps.pwNFSe.app
        print("pwNFSe.app imported successfully")
        
        import apps.dataNFSe.app
        print("dataNFSe.app imported successfully")
        
        import apps.ordens.app
        print("ordens.app imported successfully")
        
        import apps.sapNFSe.app
        print("sapNFSe.app imported successfully")
        
        # Test main app import
        import main.main as main
        print("main.py imported successfully")
        
        print("\nAll imports successful! Project structure is sound.")
        return True
        
    except Exception as e:
        print("Import error: {0}".format(e))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports()