import cv2
import os

def trim_video(input_path, output_path, skip_seconds=5):
    """
    Trim the first N seconds from a video file.
    
    Args:
        input_path: Path to input video
        output_path: Path to save trimmed video
        skip_seconds: Number of seconds to skip from the beginning
    """
    print(f"📹 Opening video: {input_path}")
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        print("❌ Error: Could not open video file")
        return False
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"📊 Video Info:")
    print(f"   FPS: {fps}")
    print(f"   Resolution: {width}x{height}")
    print(f"   Total Frames: {total_frames}")
    print(f"   Duration: {total_frames/fps:.2f} seconds")
    
    # Calculate frame to start from
    skip_frames = int(fps * skip_seconds)
    print(f"\n✂️  Trimming first {skip_seconds} seconds ({skip_frames} frames)...")
    
    # Set position to skip frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, skip_frames)
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        out.write(frame)
        frame_count += 1
        
        if frame_count % 100 == 0:
            print(f"   Processing... {frame_count} frames written")
    
    cap.release()
    out.release()
    
    print(f"\n✅ Trimmed video saved to: {output_path}")
    print(f"   New duration: {frame_count/fps:.2f} seconds")
    return True

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Find the flood footage video
    input_video = None
    for f in os.listdir(BASE_DIR):
        if f.startswith("flood_footage") and f.lower().endswith(('.mp4', '.mov', '.avi')):
            input_video = os.path.join(BASE_DIR, f)
            break
    
    if not input_video:
        print("❌ Could not find flood_footage video file!")
        exit(1)
    
    # Create output filename
    base_name = os.path.splitext(os.path.basename(input_video))[0]
    output_video = os.path.join(BASE_DIR, f"{base_name}_trimmed.mp4")
    
    # Trim the video
    success = trim_video(input_video, output_video, skip_seconds=5)
    
    if success:
        print(f"\n🎬 Done! You can now use the trimmed video:")
        print(f"   Original: {input_video}")
        print(f"   Trimmed:  {output_video}")
