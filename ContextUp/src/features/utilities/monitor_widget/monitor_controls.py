import logging
import ctypes
from ctypes import windll, byref, Structure, c_void_p, c_int, c_uint16, c_uint32, POINTER
import win32api
import win32gui
import win32con
import wmi

logger = logging.getLogger(__name__)

# GDI structs for Gamma
class RAMP(Structure):
    _fields_ = [("Red", c_uint16 * 256),
                ("Green", c_uint16 * 256),
                ("Blue", c_uint16 * 256)]

# --- Physical Monitor API Structs/Consts ---
class PHYSICAL_MONITOR(Structure):
    _fields_ = [("hPhysicalMonitor", c_void_p),
                ("szPhysicalMonitorDescription", ctypes.c_wchar * 128)]

def get_physical_monitors():
    """Get all physical monitor handles."""
    physical_monitors = []
    
    def callback(hMonitor, hdc, lprcMonitor, dwData):
        count = c_uint32()
        if windll.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(hMonitor, byref(count)):
            if count.value > 0:
                monitors = (PHYSICAL_MONITOR * count.value)()
                if windll.dxva2.GetPhysicalMonitorsFromHMONITOR(hMonitor, count.value, monitors):
                    for i in range(count.value):
                        physical_monitors.append(monitors[i].hPhysicalMonitor)
        return True

    # EnumDisplayMonitors callback type
    MONITORENUMPROC = ctypes.WINFUNCTYPE(c_int, c_void_p, c_void_p, c_void_p, c_void_p)
    windll.user32.EnumDisplayMonitors(None, None, MONITORENUMPROC(callback), 0)
    return physical_monitors


class MonitorController:
    """Controls Monitor Settings (Brightness, Refresh Rate, Night Mode)."""
    
    def __init__(self):
        try:
            self.wmi = wmi.WMI(namespace='wmi')
        except:
            self.wmi = None
            
        self._initial_settings = {}
        self._night_mode_active = False
        self._original_gamma = None
        
        # Capture initial state
        try:
            self._save_initial_state()
        except Exception as e:
            logger.error(f"Failed to save initial monitor state: {e}")

    def _save_initial_state(self):
        """Save current brightness and refresh rate."""
        # Brightness
        try:
            self._initial_settings['brightness'] = self.get_brightness()
        except:
            self._initial_settings['brightness'] = 100
            
        # Refresh Rate
        try:
            settings = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            self._initial_settings['refresh_rate'] = settings.DisplayFrequency
        except:
            self._initial_settings['refresh_rate'] = 60

    def restore_state(self):
        """Restore settings to initial state on exit."""
        logger.info("Restoring monitor settings...")
        
        # Restore Night Mode (Gamma)
        if self._night_mode_active:
            self.toggle_night_mode(False)
            
        # Restore Brightness
        if 'brightness' in self._initial_settings:
            self.set_brightness(self._initial_settings['brightness'])
            
        # Restore Refresh Rate
        if 'refresh_rate' in self._initial_settings:
            current = self.get_current_refresh_rate()
            if current != self._initial_settings['refresh_rate']:
                self.set_refresh_rate(self._initial_settings['refresh_rate'])

    # --- Brightness ---
    def get_brightness(self) -> int:
        """Get current brightness percentage (Attempts DDC/CI then WMI)."""
        # Try DDC/CI first
        try:
            handles = get_physical_monitors()
            if handles:
                min_b, cur_b, max_b = c_uint32(), c_uint32(), c_uint32()
                if windll.dxva2.GetMonitorBrightness(handles[0], byref(min_b), byref(cur_b), byref(max_b)):
                    windll.dxva2.DestroyPhysicalMonitors(len(handles), (c_void_p * len(handles))(*handles))
                    return int(cur_b.value)
        except: pass

        # Fallback to WMI
        try:
            if self.wmi:
                methods = self.wmi.WmiMonitorBrightness()
                if methods:
                    return methods[0].CurrentBrightness
        except: pass
        return 100

    def set_brightness(self, level: int):
        """Set brightness for ALL monitors (Attempts DDC/CI then WMI)."""
        success = False
        
        # Try DDC/CI (Physical Monitor API)
        try:
            handles = get_physical_monitors()
            if handles:
                for h in handles:
                    windll.dxva2.SetMonitorBrightness(h, level)
                # Cleanup handles
                windll.dxva2.DestroyPhysicalMonitors(len(handles), (c_void_p * len(handles))(*handles))
                success = True
        except Exception as e:
            logger.error(f"DDC/CI Brightness error: {e}")

        # Fallback to WMI (Laptops only usually)
        if not success and self.wmi:
            try:
                methods = self.wmi.WmiMonitorBrightnessMethods()
                if methods:
                    for m in methods:
                        m.WmiSetBrightness(level, 0)
            except Exception as e:
                logger.error(f"WMI Brightness error: {e}")

    # --- Refresh Rate ---
    def get_supported_refresh_rates(self) -> list[int]:
        """Get list of supported refresh rates for the primary display."""
        rates = set()
        i = 0
        try:
            while True:
                mode = win32api.EnumDisplaySettings(None, i)
                if not mode: break
                rates.add(mode.DisplayFrequency)
                i += 1
        except Exception:
            pass
        return sorted(list(rates))

    def get_current_refresh_rate(self) -> int:
        try:
            settings = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            return settings.DisplayFrequency
        except:
            return 60

    def set_refresh_rate(self, rate: int) -> bool:
        """Set refresh rate. Returns True if successful."""
        try:
            devmode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
            devmode.DisplayFrequency = rate
            
            # Test first
            result = win32api.ChangeDisplaySettings(devmode, win32con.CDS_TEST)
            if result != win32con.DISP_CHANGE_SUCCESSFUL:
                return False
                
            # Apply
            win32api.ChangeDisplaySettings(devmode, win32con.CDS_UPDATEREGISTRY)
            return True
        except Exception as e:
            logger.error(f"Refresh rate error: {e}")
            return False

    # --- Night Mode (Gamma) ---
    def toggle_night_mode(self, enable: bool):
        """Toggle warm gamma ramp (Red tint) for ALL monitors."""
        if enable:
            if not self._night_mode_active:
                self._night_mode_active = True
                
                # Create warm ramp (reduce Blue/Green)
                ramp = RAMP()
                for i in range(256):
                    val = i * 256
                    ramp.Red[i] = val
                    ramp.Green[i] = int(val * 0.9) # Slightly less green
                    ramp.Blue[i] = int(val * 0.8)  # Less blue
                
                self._apply_gamma_to_all(ramp)
        else:
            if self._night_mode_active:
                self._night_mode_active = False
                # Restore default linear ramp
                # (We don't cache original because different monitors might have different defaults, 
                # but resetting to linear is usually the safe 'off' state for night mode)
                
                linear_ramp = RAMP()
                for i in range(256):
                    val = i * 256
                    linear_ramp.Red[i] = val
                    linear_ramp.Green[i] = val
                    linear_ramp.Blue[i] = val
                    
                self._apply_gamma_to_all(linear_ramp)

    def _apply_gamma_to_all(self, ramp):
        """Apply gamma ramp to all active monitors."""
        
        # Callback function type for EnumDisplayMonitors
        MONITORENUMPROC = ctypes.WINFUNCTYPE(c_int, c_void_p, c_void_p, c_void_p, c_void_p)

        def _monitor_enum_proc(hMonitor, hdc, lprcMonitor, dwData):
            # Create DC for the specific monitor if hdc is null (though Enum usually provides it if we passed one? No, we passed None)
            # Actually, we need a DC for the monitor. CreateDC("DISPLAY", device_name...) 
            # OR simpler: GetMonitorInfo -> DeviceName -> CreateDC
            
            # Simplified approach: Use GetDC(None) works for primary, but for others we might need specific DC.
            # However, SetDeviceGammaRamp documentation requires a DC.
            
            # Let's try getting DC from the monitor handle context? No.
            # Correct way: Get info, Create DC.
            
            # But wait, python's ctypes callback handling can be tricky. 
            # Let's try a simpler iteration over GetSystemMetrics(80) (SM_CMONITORS) is hard.
            
            # Alternative: EnumDisplayDevices -> CreateDC.
            return True

        # Pure Python Implementation using win32api if available, else ctypes
        try:
            # win32api approach is easier if we have monitors
            monitors = win32api.EnumDisplayMonitors()
            for hMonitor, hdc, rect in monitors:
                # If hdc is None, we technically need to create one, but win32api.EnumDisplayMonitors usually returns None for hdc if we didn't pass one.
                # Use ExtCreateRegion or just CreateDC?
                
                # To set gamma, we need a DC that refers to the specific display.
                # We can create a DC for the monitor.
                monitor_info = win32api.GetMonitorInfo(hMonitor)
                device_name = monitor_info['Device']
                
                try:
                    # Create DC for this specific display
                    dc = win32gui.CreateDC("DISPLAY", device_name, None)
                    if dc:
                        windll.gdi32.SetDeviceGammaRamp(dc, byref(ramp))
                        win32gui.DeleteDC(dc)
                except Exception as e:
                    logger.error(f"Failed to set gamma for {device_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Multi-monitor Gamma Error: {e}")
            # Fallback to primary only
            hdc = windll.user32.GetDC(None)
            windll.gdi32.SetDeviceGammaRamp(hdc, byref(ramp))
            windll.user32.ReleaseDC(None, hdc)

    # --- Power Control ---
    def turn_off_monitor(self):
        """Immediately turn off all monitors (Monitor Sleep)."""
        try:
            # 0x0112 = WM_SYSCOMMAND, 0xF170 = SC_MONITORPOWER
            # 2 = Sleep, 1 = Low Power, -1 = On
            import win32gui
            import win32con
            win32gui.SendMessage(win32con.HWND_BROADCAST, 0x0112, 0xF170, 2)
        except Exception as e:
            logger.error(f"Monitor Power Error: {e}")

