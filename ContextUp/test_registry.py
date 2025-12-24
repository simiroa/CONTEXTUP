import sys
import logging
from pathlib import Path

# Setup logging to file
log_file = Path(__file__).parent / "logs" / "test_registry.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
logger.info("Starting registry test...")

# Add src to path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from core.config import MenuConfig
from core.registry import RegistryManager

try:
    # Load config (will use default path config/categories)
    logger.info("Loading configuration...")
    config = MenuConfig()
    logger.info(f"Loaded {len(config.items)} total items")
    
    # Filter sequence items
    seq_items = [item for item in config.items if 'sequence' in item.get('id', '')]
    logger.info(f"Found {len(seq_items)} sequence items:")
    for item in seq_items:
        logger.info(f"  - {item['id']}: enabled={item.get('enabled', True)}, deps={item.get('dependencies', [])}, env={item.get('environment', 'N/A')}")
    
    # Test package manager
    from manager.mgr_core.packages import PackageManager
    pm = PackageManager(Path(__file__).parent)
    pm.refresh_package_cache()
    installed = pm.get_installed_packages()
    
    logger.info(f"Installed packages: {len(installed)} total")
    logger.info(f"  - customtkinter: {'customtkinter' in installed}")
    logger.info(f"  - pillow: {'pillow' in installed}")
    
    # Check dependencies for each sequence item
    logger.info("\nChecking dependencies:")
    for item in seq_items:
        valid, missing = pm.check_dependencies(item, installed)
        logger.info(f"  - {item['id']}: valid={valid}, missing={missing}")
    
    # Register
    logger.info("\n" + "="*50)
    logger.info("Starting registration...")
    logger.info("="*50)
    
    registry = RegistryManager(config)
    registry.register_all()
    
    logger.info("\nRegistration complete!")
    logger.info(f"Check log file: {log_file}")
    
except Exception as e:
    logger.error(f"Registration failed: {e}", exc_info=True)
    raise
