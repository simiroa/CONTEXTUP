# Phase 4 AI Setup - Conda Environment

## RTX 3080 Ti (12GB VRAM) - Excellent for all AI features! 🎉

### Recommended Approach: Conda Environment

**Why Conda?**
- Better dependency management
- Isolated from system Python
- Easier CUDA toolkit management
- Can use optimized builds (Intel MKL, etc.)

---

## Setup Instructions

### 1. Create Conda Environment

```bash
# Create new environment for AI tools
conda create -n ai_tools python=3.10 -y
conda activate ai_tools
```

### 2. Install PyTorch with CUDA 12.1

```bash
# Install PyTorch optimized for RTX 3080 Ti
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia -y
```

### 3. Install AI Dependencies

```bash
# Core dependencies
pip install transformers diffusers accelerate
pip install opencv-python pillow einops
pip install timm safetensors

# Optional but recommended
pip install xformers  # Faster attention (for SUPIR)
```

---

## Optimized Model Recommendations for RTX 3080 Ti

### Background Removal
**Recommended**: All 3 models will run smoothly

1. **RMBG-2.0** (Best balance)
   - Speed: ~0.5s per image
   - Quality: Excellent
   - VRAM: ~2GB

2. **BiRefNet** (Highest quality)
   - Speed: ~1s per image
   - Quality: Best
   - VRAM: ~3GB

3. **InSPyReNet** (Fastest)
   - Speed: ~0.3s per image
   - Quality: Good
   - VRAM: ~1.5GB

**Suggestion**: Implement all 3 and let user choose in GUI

---

### Frame Interpolation
**Recommended**: RIFE v4.6 + IFRNet (dual option)

1. **RIFE v4.6**
   - Speed: ~30fps processing (1080p)
   - Quality: Excellent
   - VRAM: ~4GB
   - Best for: General use

2. **IFRNet**
   - Speed: ~60fps processing (1080p)
   - Quality: Very Good
   - VRAM: ~2GB
   - Best for: Speed priority

**Your GPU**: Can handle 4K video interpolation!

---

### Advanced Image Upscaling

**Better Alternative to SUPIR**: Use **Tile-based approach**

1. **RealESRGAN** (already have) - Fast baseline
2. **SwinIR-Large** - Better quality, similar speed
3. **HAT** (Hybrid Attention Transformer) - Best quality

**For RTX 3080 Ti**:
- Can upscale 4K images directly
- Use tile processing for 8K+
- Batch processing: 4-8 images simultaneously

**Recommendation**: 
```python
# Offer quality tiers
- Fast: RealESRGAN (2-4x, ~1s)
- Balanced: SwinIR (2-4x, ~3s)
- Best: HAT (2-4x, ~5s)
```

---

### Video Upscaling

**Better Alternative to FlashVSR**: **RealBasicVSR**

**Why RealBasicVSR?**
- More mature and stable
- Better quality than FlashVSR
- Optimized for RTX 30-series
- Active development

**Performance on RTX 3080 Ti**:
- 1080p → 4K: ~15fps processing
- 720p → 1080p: ~30fps processing
- VRAM usage: ~6-8GB

**Alternative**: **EDVR** (even faster, slightly lower quality)

---

## Enhanced Implementation Plan

### Phase 4A: Background Removal (Week 1)
```python
# Implement 3 models with selection dialog
class BackgroundRemovalDialog:
    models = {
        'Fast': 'InSPyReNet',
        'Balanced': 'RMBG-2.0', 
        'Best': 'BiRefNet'
    }
```

### Phase 4B: Frame Interpolation (Week 2)
```python
# Dual-mode interpolation
class FrameInterpolationDialog:
    modes = {
        'Fast (IFRNet)': '2-4x speed',
        'Quality (RIFE)': 'Best results'
    }
    target_fps = [24, 30, 60, 120]
```

### Phase 4C: Advanced Upscaling (Week 3)
```python
# Three-tier upscaling
class AdvancedUpscaleDialog:
    tiers = {
        'Fast': 'RealESRGAN',
        'Balanced': 'SwinIR',
        'Best': 'HAT'
    }
    scales = [2, 3, 4]
```

### Phase 4D: Video Upscaling (Week 4)
```python
# RealBasicVSR with progress bar
class VideoUpscaleDialog:
    models = {
        'Fast': 'EDVR',
        'Best': 'RealBasicVSR'
    }
```

---

## Storage Requirements (Updated)

| Feature | Model Size | VRAM Usage | Processing Speed |
|---------|-----------|------------|------------------|
| BG Removal (all 3) | ~5GB | 2-3GB | 0.3-1s/image |
| RIFE + IFRNet | ~150MB | 2-4GB | 30-60fps |
| HAT + SwinIR | ~500MB | 4-6GB | 3-5s/image |
| RealBasicVSR | ~200MB | 6-8GB | 15-30fps |
| **Total** | **~6GB** | **Peak: 8GB** | - |

**Your 12GB VRAM**: Perfect! Can run everything with headroom.

---

## Next Steps

1. **Setup Conda environment** (5 min)
2. **Install PyTorch + dependencies** (10 min)
3. **Implement Background Removal** with 3-model selection (Priority 1)
4. **Test with your GPU** - should be very fast!
5. **Expand to other features** based on performance

Ready to proceed?
