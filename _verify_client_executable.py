def _verify_client_executable(self) -> bool:
    """
    Verify that the Client.py is properly executable with appropriate permissions.
    
    This method performs checks to ensure that:
    1. The client file exists
    2. The file has appropriate permissions
    3. The file can be executed (performs a non-destructive test)
    
    Returns:
        bool: True if the client is verified as executable, False otherwise
    """
    try:
        import os
        import stat
        
        client_path = self.install_path / "Client.py"
        
        # Step 1: Verify file existence
        if not client_path.exists():
            print(f"[ERR] Client.py does not exist at: {client_path}")
            return False
        
        # Step 2: Check file size
        file_size = client_path.stat().st_size
        if file_size < 1000:  # Client script should be substantial
            print(f"[WARNING] Client.py appears too small ({file_size} bytes)")
            
        # Step 3: Check file permissions
        try:
            # Check if file is readable and executable
            is_executable = os.access(client_path, os.X_OK)
            is_readable = os.access(client_path, os.R_OK)
            
            if not is_readable:
                print(f"[WARNING] Client.py is not readable")
                
            if not is_executable:
                print(f"[WARNING] Client.py is not marked as executable")
                
            # On Windows, the X_OK check may not be reliable,
            # so we'll also check the file mode directly
            if self.system == "Windows":
                file_mode = client_path.stat().st_mode
                if not (file_mode & stat.S_IEXEC):
                    print(f"[WARNING] Client.py does not have executable permissions")
        except Exception as e:
            print(f"[WARNING] Could not check file permissions: {e}")
            
        # Step 4: Try a non-destructive execution test on Windows
        # This checks if Python can at least parse the file without errors
        if self.system == "Windows":
            import subprocess
            try:
                # Use Python to check syntax without executing
                result = subprocess.run(
                    [sys.executable, "-m", "py_compile", str(client_path)],
                    check=False,
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if result.returncode != 0:
                    print(f"[WARNING] Client.py has syntax errors: {result.stderr}")
                    return False
            except Exception as e:
                print(f"[WARNING] Could not verify client syntax: {e}")
                return False
                
        # If we reach here, the client is likely executable
        return True
        
    except Exception as e:
        print(f"[ERR] Failed to verify client executable: {e}")
        import traceback
        traceback.print_exc()
        return False
