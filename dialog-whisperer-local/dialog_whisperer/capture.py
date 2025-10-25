"""Screen capture tools using mss and PIL (lazy imports)."""

def compare_images(img1, img2, threshold=0.80):
    """Compare two images and return True if they are similar.
    
    Args:
        img1: PIL.Image
        img2: PIL.Image
        threshold: float between 0 and 1, higher means more similar
        
    Returns:
        bool: True if images are similar
    """
    try:
        import numpy as np
        from PIL import ImageFilter
    except Exception as e:
        raise ImportError("numpy and Pillow are required for image comparison: %s" % e)
        
    # Convert to grayscale and numpy arrays
    if img1.size != img2.size:
        return False
        
    # Apply slight blur to reduce impact of small movements/changes
    gray1 = img1.convert('L').filter(ImageFilter.GaussianBlur(radius=2))
    gray2 = img2.convert('L').filter(ImageFilter.GaussianBlur(radius=2))
    
    # Convert to numpy arrays and normalize
    arr1 = np.array(gray1).astype('float32') / 255
    arr2 = np.array(gray2).astype('float32') / 255
    
    # Calculate structural similarity
    # Break the image into blocks and compare
    block_size = 16
    h, w = arr1.shape
    num_blocks_h = h // block_size
    num_blocks_w = w // block_size
    
    similarities = []
    for i in range(num_blocks_h):
        for j in range(num_blocks_w):
            y1 = i * block_size
            y2 = (i + 1) * block_size
            x1 = j * block_size
            x2 = (j + 1) * block_size
            
            block1 = arr1[y1:y2, x1:x2]
            block2 = arr2[y1:y2, x1:x2]
            
            # Calculate similarity for this block
            mse = np.mean((block1 - block2) ** 2)
            similarities.append(1 - mse)
    
    # Get the median similarity across all blocks
    # This makes the comparison more robust to small changes
    similarity = np.median(similarities)
    
    return similarity >= threshold

def capture_region(bbox=None):
    """Capture a screen region and return a PIL Image.

    Args:
        bbox: tuple (left, top, right, bottom) or None for full screen

    Returns:
        PIL.Image
    
    Raises:
        ValueError: If the bounding box has zero or negative size
        ImportError: If required dependencies are not available
    """
    try:
        import mss
        from PIL import Image
        import numpy as np
    except Exception as e:
        raise ImportError("mss, Pillow and numpy are required for capture: %s" % e)

    with mss.mss() as sct:
        if bbox is None:
            monitor = sct.monitors[0]
        else:
            left, top, right, bottom = bbox
            # Handle negative coordinates
            width = right - left
            height = bottom - top
            
            # Check for invalid dimensions
            if width <= 0 or height <= 0:
                raise ValueError("Invalid bounding box dimensions: box must have positive width and height")
            
            # Adjust negative coordinates to screen bounds
            left = max(0, left)
            top = max(0, top)
            monitor = {"left": left, "top": top, "width": width, "height": height}
        sct_img = sct.grab(monitor)
        arr = np.asarray(sct_img)
        # mss returns BGRA
        img = Image.fromarray(arr[:, :, :3][:, :, ::-1])
        return img
