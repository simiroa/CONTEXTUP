"""
Test psutil port -> PID -> process mapping capabilities
"""
import psutil

print("=== psutil net_connections test ===\n")

# Get all listening connections
try:
    conns = psutil.net_connections(kind='inet')
    listen = [c for c in conns if c.status == 'LISTEN']
    
    print(f"Total connections: {len(conns)}")
    print(f"Listening ports: {len(listen)}\n")
    
    print("=== Port | PID | Process Name | Executable Path ===\n")
    
    for c in listen[:20]:
        if c.pid:
            try:
                proc = psutil.Process(c.pid)
                name = proc.name()
                try:
                    exe = proc.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    exe = "Access Denied"
                try:
                    cmdline = ' '.join(proc.cmdline()[:3])
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cmdline = ""
                    
                print(f":{c.laddr.port:<6} PID {c.pid:<8} {name:<25} {exe[:60]}")
                if cmdline and cmdline != name:
                    print(f"         cmdline: {cmdline[:80]}")
            except psutil.NoSuchProcess:
                print(f":{c.laddr.port:<6} PID {c.pid} - Process no longer exists")
        else:
            print(f":{c.laddr.port:<6} PID N/A")
            
except Exception as e:
    print(f"Error: {e}")
