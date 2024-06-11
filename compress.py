import subprocess
import os

def convert_video(input_file_path, size=5):
    try:
        # Check if the file exists and is accessible
        if not os.path.exists(input_file_path):
            raise Exception("Input file does not exist.")

        # Ensure the file has read permissions
        os.chmod(input_file_path, 0o644)

        # Get input video duration
        duration_cmd = [
            'ffprobe', '-i', input_file_path, '-show_entries', 'format=duration', 
            '-v', 'quiet', '-of', 'csv=p=0'
        ]
        try:
            duration_result = subprocess.check_output(duration_cmd).decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"ffprobe failed: {e}")

        if not duration_result:
            raise Exception("Failed to get video duration.")
        duration = float(duration_result)

        # Calculate target bitrate to keep the file size under specified size (in MB)
        target_bitrate = int((size * 8 * 1024 * 1024) / (duration * 1000))

        # Run ffmpeg command to resize and compress the video
        output_file = f'/tmp/output_video_{size}MB.mp4'
        ffmpeg_cmd = [
            'ffmpeg', '-i', input_file_path,
            '-vf', 'scale=-2:480',
            '-b:v', f'{target_bitrate}k',
            '-maxrate', f'{target_bitrate}k',
            '-bufsize', f'{2*target_bitrate}k',
            '-c:a', 'aac',  # Use AAC codec for audio
            '-b:a', '128k',  # Set audio bitrate to 128kbps
            '-af', 'anlmdn',  # Apply noise reduction filter
            output_file
        ]
        subprocess.run(ffmpeg_cmd, check=True)

        # Read the converted video data
        with open(output_file, 'rb') as f:
            converted_video_data = f.read()

        # Clean up temporary files
        os.remove(output_file)

        return converted_video_data

    except subprocess.CalledProcessError as e:
        raise Exception(f"Conversion failed: {e}")
    except Exception as e:
        raise Exception(f"An unexpected error occurred: {e}")

# Call the function with the path to your input video file
#converted_video = convert_video('yc.mp4')
#print(convert_video)